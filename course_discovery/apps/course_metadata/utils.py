import logging
import random
import string
from collections import Counter
from functools import reduce
from itertools import combinations, chain
from pprint import pformat

import requests
from django.utils.functional import cached_property
from stdimage.models import StdImageFieldFile
from stdimage.utils import UploadTo

from course_discovery.apps.core.models import Partner
from course_discovery.apps.course_metadata.choices import ProgramStatus
from course_discovery.apps.course_metadata.constants import RULES_PROGRAM_TYPE_NAME, PROGRAM_RULES
from course_discovery.apps.course_metadata.exceptions import MarketingSiteAPIClientException

RESERVED_ELASTICSEARCH_QUERY_OPERATORS = ('AND', 'OR', 'NOT', 'TO',)

logger = logging.getLogger(__name__)


def clean_query(query):
    """ Prepares a raw query for search.

    Args:
        query (str): query to clean.

    Returns:
        str: cleaned query
    """
    # Ensure the query is lowercase, since that is how we index our data.
    query = query.lower()

    # Specifying a SearchQuerySet filter will append an explicit AND clause to the query, thus changing its semantics.
    # So we wrap parentheses around the original query in order to preserve the semantics.
    query = '({qs})'.format(qs=query)

    # Ensure all operators are uppercase
    for operator in RESERVED_ELASTICSEARCH_QUERY_OPERATORS:
        old = ' {0} '.format(operator.lower())
        new = ' {0} '.format(operator.upper())
        query = query.replace(old, new)

    return query


class UploadToFieldNamePath(UploadTo):
    """
    This is a utility to create file path for uploads based on instance field value
    """
    def __init__(self, populate_from, **kwargs):
        self.populate_from = populate_from
        super(UploadToFieldNamePath, self).__init__(populate_from, **kwargs)

    def __call__(self, instance, filename):
        field_value = getattr(instance, self.populate_from)
        self.kwargs.update({
            'name': field_value
        })
        return super(UploadToFieldNamePath, self).__call__(instance, filename)


def custom_render_variations(file_name, variations, storage, replace=True):
    """ Utility method used to override default behaviour of StdImageFieldFile by
    passing it replace=True.

    Args:
        file_name (str): name of the image file.
        variations (dict): dict containing variations of image
        storage (Storage): Storage class responsible for storing the image.

    Returns:
        False (bool): to prevent its default behaviour
    """

    for variation in variations.values():
        StdImageFieldFile.render_variation(file_name, variation, replace, storage)

    # to prevent default behaviour
    return False


class MarketingSiteAPIClient(object):
    """
    The marketing site API client we can use to communicate with the marketing site
    """
    username = None
    password = None
    api_url = None

    def __init__(self, marketing_site_api_username, marketing_site_api_password, api_url):
        if not (marketing_site_api_username and marketing_site_api_password):
            raise MarketingSiteAPIClientException('Marketing Site API credentials are not properly configured!')
        self.username = marketing_site_api_username
        self.password = marketing_site_api_password
        self.api_url = api_url.strip('/')

    @cached_property
    def init_session(self):
        # Login to set session cookies
        session = requests.Session()
        login_url = '{root}/user'.format(root=self.api_url)
        login_data = {
            'name': self.username,
            'pass': self.password,
            'form_id': 'user_login',
            'op': 'Log in',
        }
        response = session.post(login_url, data=login_data)
        admin_url = '{root}/admin'.format(root=self.api_url)
        # This is not a RESTful API so checking the status code is not enough
        # We also check that we were redirected to the admin page
        if not (response.status_code == 200 and response.url == admin_url):
            raise MarketingSiteAPIClientException(
                {
                    'message': 'Marketing Site Login failed!',
                    'status': response.status_code,
                    'url': response.url
                }
            )
        return session

    @property
    def api_session(self):
        self.init_session.headers.update(self.headers)
        return self.init_session

    @property
    def csrf_token(self):
        # We need to make sure we can bypass the Varnish cache.
        # So adding a random salt into the query string to cache bust
        random_qs = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        token_url = '{root}/restws/session/token?cachebust={qs}'.format(root=self.api_url, qs=random_qs)
        response = self.init_session.get(token_url)
        if not response.status_code == 200:
            raise MarketingSiteAPIClientException({
                'message': 'Failed to retrieve Marketing Site CSRF token!',
                'status': response.status_code,
            })
        token = response.content.decode('utf8')
        return token

    @cached_property
    def user_id(self):
        # Get a user ID
        user_url = '{root}/user.json?name={username}'.format(root=self.api_url, username=self.username)
        response = self.init_session.get(user_url)
        if not response.status_code == 200:
            raise MarketingSiteAPIClientException('Failed to retrieve Marketing site user details!')
        user_id = response.json()['list'][0]['uid']
        return user_id

    @property
    def headers(self):
        return {
            'Content-Type': 'application/json',
            'X-CSRF-Token': self.csrf_token,
        }


def compute_bundles():
    """
    Performs evaluating of possible bundles (based on specified rules).

    See: course_metadata.constants
    """
    from course_discovery.apps.course_metadata.models import Course

    def get_rules_types():
        rules_types_set = set()
        for rule in PROGRAM_RULES:
            rule_types = set(key for key in rule.keys() if isinstance(key, str) and key != 'name')
            rules_types_set.update(rule_types)
        return rules_types_set

    def get_courses_data():
        """
        Fetches course data dict from Course model.
        """
        rules_types = get_rules_types()
        courses_data = []
        courses = Course.objects.exclude(program_duration__isnull=True)

        for course in courses:
            course_item = {
                'uuid': course.uuid,
                'duration': course.program_duration,
            }
            if course.program_type is not None:
                if course.program_type in rules_types:
                    course_item['type'] = course.program_type
                else:
                    logger.warn(
                        "Found course with `program type` which is absent in Bundling rules! "
                        "(Type: `%s` is ignored - rules must be extended with this type to make it affect)",
                        course.program_type
                    )
            courses_data.append(course_item)

        return courses_data

    def process_rules(rules):
        rule_bundles = {}
        logger.debug('Getting courses data...')
        courses_data = get_courses_data()
        logger.info('...found {} course(s) for bundling.'.format(len(courses_data)))

        logger.info('Processing rules...')
        logger.debug('*' * 120)
        for i, rule in enumerate(rules, 1):
            logger.debug('\nApplying rule {}'.format(i))
            bundles = apply_rule(rule, courses_data)
            rule_bundles[rule['name']] = bundles
        logger.info(
            'Total count of possible bundles: %d',
            reduce(lambda x, y: x + len(y), rule_bundles.values(), 0)
        )
        return rule_bundles

    def apply_rule(rule, courses):
        assert isinstance(rule, dict)
        specials = {}  # courses' program types
        rule_dict = rule.copy()
        rule_name = rule_dict.pop('name')
        for key in rule.keys():
            if isinstance(key, str) and key != 'name':
                specials[key] = rule_dict.pop(key)
        total_hours = reduce(lambda x, y: x + y[0] * y[1], rule_dict.items(), 0)
        total_courses = sum(rule_dict.values())

        logger.debug('- rule {}: "{}"'.format(rule_name, rule_dict))
        logger.debug(
            '- special restrictions: {}'.format(len(specials) and '%d (%s)' % (len(specials), specials))
        )
        logger.debug('- total bundle hours: {}'.format(total_hours))
        logger.debug('- courses in bundle: {}'.format(total_courses))
        logger.debug('processing...')

        target_courses_list = list(filter_courses(courses, rule_dict, specials))

        logger.debug(
            'Forming from: %d course(s): \n%s', len(target_courses_list), pformat(target_courses_list)
        )
        logger.debug('-' * 120)

        combs_list = compute_combinations(target_courses_list, total_courses)
        if not combs_list:
            logger.debug('\n...there no possible combinations for the rule.',)
            return combs_list
        else:
            logger.debug('...there %d combination(s) in total...', len(combs_list))


        # filtering course combinations based on rule's duration formula:
        def remove_redundant(combination):
            counter = Counter(map(lambda c: c['duration'], combination))
            etalon = Counter(rule_dict)
            return counter == etalon

        bundles_list = list(filter(remove_redundant, combs_list))
        logger.debug('...there %d combination(s) after rule comparison...', len(bundles_list))

        # processing `required` course type rule:
        def remove_required(combination):
            return bool(set(map(lambda c: c.get('type'), combination)).intersection(required_types_list))

        required_types_list = list(filter(lambda k: specials[k], specials.keys()))
        if required_types_list:
            bundles_list = list(filter(remove_required, bundles_list))
            logger.debug('...there %d combination(s) after `required` rule applying...', len(bundles_list))

        logger.debug('Bundles created [%d]: \n%s', len(bundles_list), pformat(bundles_list))
        return bundles_list

    def filter_courses(courses, rule_dict, specials):
        """
        Excludes not conditional courses.

        Excludes courses with not appropriate duration.
        Excludes courses with not appropriate program type (type isn't include).
        :param courses: all courses data
        :param rule_dict: `quantitative` rule part (e.g.: {7:2, 8:1})
        :param specials: `qualitative` rule part  (e.g.: {'spec': True, 'other': False})
        :return: filter obj
        """
        filter_duration = filter(lambda c: c['duration'] in rule_dict.keys(), courses)
        filter_specials = filter(
            lambda c: c.get('type') is None or not bool(specials) or specials[c.get('type')],
            filter_duration
        )
        return filter_specials

    def compute_combinations(courses, r):
        return list(combinations(courses, r))

    logger.debug('Found {} rules.'.format(len(PROGRAM_RULES)))
    bundles_variants = process_rules(PROGRAM_RULES)
    logger.debug("Computed bundles variants: \n %s", pformat(bundles_variants))
    return bundles_variants


def create_programs():
    """
    Create Program model objects based on computed bundles.
    """
    from course_discovery.apps.course_metadata.models import Course, Program, ProgramType

    partner = Partner.objects.first()  # we don't expect more then one here
    bundles_dict = compute_bundles()
    ruled_programs = None

    logger.debug('Preparing for programs creation...')

    p_type, created = ProgramType.objects.get_or_create(name=RULES_PROGRAM_TYPE_NAME)
    if created:
        logger.debug(
            '...new ProgramType [name=%s] created for `automated` programs',
            RULES_PROGRAM_TYPE_NAME
        )
        logger.debug('...so, there are no `automated` programs yet')
    else:
        ruled_programs = Program.objects\
            .filter(type__name=RULES_PROGRAM_TYPE_NAME)\
            .prefetch_related('courses')
        logger.debug(
            '...found {} already created `automated` program(s)...'.format(ruled_programs.count())
        )

    generated = 0
    skipped = 0

    def already_exists(title, bundle, programs):
        bundle_set = set(map(lambda c: c['uuid'], bundle))
        for program in programs:
            if program.title == title:
                return True
            presented_set = set(program.courses.values_list('uuid', flat=True))
            if bundle_set == presented_set:
                return True
        return False

    for rule_name, bundles in bundles_dict.items():
        for i, bundle in enumerate(bundles, 1):
            title = 'Program-{} {}'.format(i, rule_name)

            if ruled_programs and already_exists(title, bundle, ruled_programs):
                logger.info("Program with title: %s already exists. Skipping...", title)
                skipped += 1
                continue
            program = Program(
                title=title,
                status=ProgramStatus.Active,
                type=p_type,
                partner=partner,
                marketing_slug='{}-program-{}'.format(rule_name, i),
            )
            program.save()
            generated += 1
            program.courses = Course.objects.filter(uuid__in=map(lambda c: c['uuid'], bundle))
            program.save()

    logger.info(
        "Created {} new program(s)! Skipped {} (already presented)".format(generated, skipped)
    )
    return generated
