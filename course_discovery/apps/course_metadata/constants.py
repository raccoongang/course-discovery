COURSE_ID_REGEX = r'[^/+]+(/|\+)[^/+]+'
COURSE_RUN_ID_REGEX = r'[^/+]+(/|\+)[^/+]+(/|\+)[^/]+'

# Rules for automated Programs creation:
RULES_PROGRAM_TYPE_NAME = 'Rules'
PROGRAM_RULES = [
    {'name': '7/2-USPAP', 7: 2, 'uspap': False},
    {'name': '7/2+USPAP', 7: 2, 'uspap': True},
    {'name': '7/3', 7: 3},
    {'name': '8/1|7/1|3/2', 8: 1, 7: 1, 3: 2},
    {'name': '7/2|3/2-USPAP', 7: 2, 3: 2, 'uspap': False},
    {'name': '7/4', 7: 4},
    {'name': '8/1|7/2|3/2', 8: 1, 7: 2, 3: 2},
    {'name': '7/3|3/3', 7: 3, 3: 3},
    {'name': '8/1|7/5|4/1|3/1', 8: 1, 7: 5, 4: 1, 3: 1},
]
