import logging

from django.core.management import BaseCommand

from course_discovery.apps.core.models import Partner
from course_discovery.apps.course_metadata.models import Program
from course_discovery.apps.course_metadata.tests.factories import (
    CorporateEndorsementFactory, CourseFactory, CourseRunFactory, EndorsementFactory, ExpectedLearningItemFactory,
    FAQFactory, JobOutlookItemFactory, OrganizationFactory, ProgramFactory
)
from course_discovery.apps.course_metadata.utils import create_programs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create programs based on predefined rules.'

    def handle(self, *args, **options):
        self.generate_programs()

    @staticmethod
    def generate_programs():
        logger.info('Automated programs generation started...')
        create_programs()
        logging.info('Automated programs generation completed!')
