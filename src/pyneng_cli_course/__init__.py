__version__ = "3.1.3"

ANSWERS_URL = "https://github.com/pyneng/pyneng-course-answers"
# needed for tasks/tests updates
TASKS_URL = "https://github.com/pyneng/pyneng-course-tasks"
DEFAULT_BRANCH = "main"
STUDENT_REPO_TEMPLATE = r"online-\d+-\w+-\w+"
TASK_DIRS = [
    "04_data_structures",
    "05_basic_scripts",
    "06_control_structures",
    "07_files",
    "09_functions",
    "11_modules",
    "12_useful_modules",
    "15_module_re",
    "17_serialization",
    "18_ssh_telnet",
    "19_concurrent_connections",
    "20_jinja2",
    "21_textfsm",
    "22_oop_basics",
    "23_oop_special_methods",
    "24_oop_inheritance",
    "25_db",
]
TASK_NUMBER_DIR_MAP = {
    4: "04_data_structures",
    5: "05_basic_scripts",
    6: "06_control_structures",
    7: "07_files",
    9: "09_functions",
    11: "11_modules",
    12: "12_useful_modules",
    15: "15_module_re",
    17: "17_serialization",
    18: "18_ssh_telnet",
    19: "19_concurrent_connections",
    20: "20_jinja2",
    21: "21_textfsm",
    22: "22_oop_basics",
    23: "23_oop_special_methods",
    24: "24_oop_inheritance",
    25: "25_db",
}

DB_TASK_DIRS = [
    "task_25_1",
    "task_25_2",
    "task_25_3",
    "task_25_4",
    "task_25_5",
    "task_25_5a",
    "task_25_6",
]

# from importlib import resources
# import json
#
# Read URL from config file
# _cfg = json.loads(resources.read_text("pyneng", "config.json"))
# ANSWERS_URL = _cfg["answers_url"]
# TASKS_URL = _cfg["tasks_url"]

