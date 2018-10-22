COURSE_ID_REGEX = r'[^/+]+(/|\+)[^/+]+'
COURSE_RUN_ID_REGEX = r'[^/+]+(/|\+)[^/+]+(/|\+)[^/]+'

# Rules for automated Programs creation:
RULES_PROGRAM_TYPE_NAME = 'Bundles'
PROGRAM_RULES = [
    {
        'name': '[14 Hour Bundle] Two 7-hour courses',
        7: 2,
        'uspap': False
    },
    {
        'name': '[14 Hour Bundle] 7-hour course and 2018-2019 USPAP course',
        7: 2,
        'uspap': True
    },
    {
        'name': '[21 Hour Bundle] Three 7 hour courses',
        7: 3,
        'uspap': False
    },
    {
        'name': '[21 Hour Bundle] 8-hour course, 7-hour course and two 3-hour courses',
        8: 1, 7: 1, 3: 2,
        'uspap': False
    },
    {
        'name': '[20 Hour Bundle] Two 7-hour courses and two 3-hour courses',
        7: 2, 3: 2,
        'uspap': False
    },
    {
        'name': '[28 Hour Bundle] Four 7-hour courses',
        7: 4,
    },
    {
        'name': '[28 Hour Bundle] Two 7-hour courses, one 8-hour course and two 3-hour courses',
        8: 1, 7: 2, 3: 2,
    },
    {
        'name': '[30 Hour Bundle] Three 7-hour courses and three 3-hour courses',
        7: 3, 3: 3,
    },
    {
        'name': '[50 Hour Bundle] Five 7-hour courses, 8-hour course, 4-hour course and 3-hour course',
        8: 1, 7: 5, 4: 1, 3: 1,
        'uspap': True
    },
]

BUNDLE_TYPE_MAPPING = {
    '[14 Hour Bundle] Two 7-hour courses': '14',
    '[14 Hour Bundle] 7-hour course and 2018-2019 USPAP course': '14:uspap',
    '[21 Hour Bundle] Three 7 hour courses': '21',
    '[21 Hour Bundle] 8-hour course, 7-hour course and two 3-hour courses': '21',
    '[20 Hour Bundle] Two 7-hour courses and two 3-hour courses': '20',
    '[28 Hour Bundle] Four 7-hour courses': '28',
    '[28 Hour Bundle] Two 7-hour courses, one 8-hour course and two 3-hour courses': '28',
    '[30 Hour Bundle] Three 7-hour courses and three 3-hour courses': '30',
    '[50 Hour Bundle] Five 7-hour courses, 8-hour course, 4-hour course and 3-hour course': '50'
}

BUNDLES_PRICES = {
    '[14 Hour Bundle] 7-hour course and 2018-2019 USPAP course': 199,
    '[21 Hour Bundle] Three 7 hour courses': 269,
    '[21 Hour Bundle] 8-hour course, 7-hour course and two 3-hour courses': 289,
    '[20 Hour Bundle] Two 7-hour courses and two 3-hour courses': 259,
    '[28 Hour Bundle] Four 7-hour courses': 449,
    '[28 Hour Bundle] Two 7-hour courses, one 8-hour course and two 3-hour courses': 449,
    '[30 Hour Bundle] Three 7-hour courses and three 3-hour courses': 469,
    '[50 Hour Bundle] Five 7-hour courses, 8-hour course, 4-hour course and 3-hour course': 599,
}
