__version__ = "3.0.0"

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

