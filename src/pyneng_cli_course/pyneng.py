import sys
import re
import os
import json
from glob import glob

import click
import pytest
from pytest_jsonreport.plugin import JSONReport

from pyneng_cli_course import (
    DEFAULT_BRANCH,  # непонятно работает ли оно в связке с utils
    TASK_DIRS,
    DB_TASK_DIRS,
)
from pyneng_cli_course.exceptions import PynengError
from pyneng_cli_course.utils import (
    red,
    green,
    save_changes_to_github,
    test_run_for_github_token,
    send_tasks_to_check,
    current_chapter_id,
    current_dir_name,
    parse_json_report,
    copy_answers,
    update_tasks_and_tests,
)


def exception_handler(exception_type, exception, traceback):
    """
    sys.excepthook для отключения traceback по умолчанию
    """
    print(f"\n{exception_type.__name__}: {exception}\n")


def _get_tasks_tests_from_cli(self, value):
    regex = (
        r"(?P<all>all)|"
        r"(?P<number_star>\d\*)|"
        r"(?P<letters_range>\d[a-i]-[a-i])|"
        r"(?P<numbers_range>\d-\d)|"
        r"(?P<single_task>\d[a-i]?)"
    )
    tasks_list = re.split(r"[ ,]+", value)
    current_chapter = current_chapter_id()
    test_files = []
    task_files = []
    for task in tasks_list:
        match = re.fullmatch(regex, task)
        if match:
            if task == "all":
                test_files = sorted(glob(f"test_task_{current_chapter}_*.py"))
                task_files = sorted(glob(f"task_{current_chapter}_*.py"))
                break
            else:
                if match.group("letters_range"):
                    task = f"{task[0]}[{task[1:]}]"  # convert 1a-c to 1[a-c]
                elif match.group("numbers_range"):
                    task = f"[{task}]"  # convert 1-3 to [1-3]

                test_files += glob(f"test_task_{current_chapter}_{task}.py")
                task_files += glob(f"task_{current_chapter}_{task}.py")
        else:
            self.fail(
                red(
                    f"Данный формат не поддерживается {task}. "
                    "Допустимые форматы: 1, 1a, 1b-d, 1*, 1-3"
                )
            )
    tasks_with_tests = set([test.replace("test_", "") for test in test_files])
    tasks_without_tests = set(task_files) - tasks_with_tests
    return sorted(test_files), sorted(tasks_without_tests), sorted(task_files)


class CustomTasksType(click.ParamType):
    """
    Класс создает новый тип для click и преобразует
    допустимые варианты строк заданий в отдельные файлы тестов.

    Кроме того проверяет есть ли такой файл в текущем каталоге
    и оставляет только те, что есть.
    """

    name = "CustomTasksType"

    def convert(self, value, param, ctx):
        if isinstance(value, tuple):
            return value

        current_chapter = current_dir_name()
        if current_chapter not in TASK_DIRS + DB_TASK_DIRS:
            task_dirs_line = "\n    ".join(
                [d for d in TASK_DIRS if not d.startswith("task")]
            )
            self.fail(
                red(
                    f"\nСкрипт нужно вызывать из каталогов с заданиями:"
                    f"\n    {task_dirs_line}"
                )
            )

        return _get_tasks_tests_from_cli(self, value)


@click.command(
    context_settings=dict(
        ignore_unknown_options=True, help_option_names=["-h", "--help"]
    )
)
@click.argument("tasks", default="all", type=CustomTasksType())
@click.option(
    "--disable-verbose", "-d", is_flag=True, help="Отключить подробный вывод pytest"
)
@click.option(
    "--answer",
    "-a",
    is_flag=True,
    help=(
        "Скопировать ответы для заданий, которые "
        "прошли тесты. При добавлении этого флага, "
        "не выводится traceback для тестов."
    ),
)
@click.option(
    "--check",
    "-c",
    is_flag=True,
    help=(
        "Сдать задания на проверку. "
        "При добавлении этого флага, "
        "не выводится traceback для тестов."
    ),
)
@click.option("--debug", is_flag=True, help="Показывать traceback исключений")
@click.option("--default-branch", "-b", default="main")
@click.option("--test-token", is_flag=True, help="Проверить работу токена")
@click.option(
    "--all",
    "git_add_all_to_github",
    is_flag=True,
    help="Добавить git add .",
)
@click.option("--ignore-ssl-cert", default=False)
@click.version_option(version="2.3.3")
@click.option(
    "--update", "update_tasks_tests", is_flag=True, help="Обновить задания и тесты"
)
@click.option(
    "--test-only", "update_tests_only", is_flag=True, help="Обновить только тесты"
)
@click.option(
    "--save-all",
    "save_all_to_github",
    is_flag=True,
    help="Сохранить на GitHub все измененные файлы в текущем каталоге",
)
def cli(
    tasks,
    disable_verbose,
    answer,
    check,
    debug,
    default_branch,
    test_token,
    git_add_all_to_github,
    ignore_ssl_cert,
    update_tasks_tests,
    update_tests_only,
    save_all_to_github,
):
    """
    Запустить тесты для заданий TASKS. По умолчанию запустятся все тесты.

    \b
    Эти флаги не запускают тестирование заданий
      pyneng --test-token          Проверить работу токена
      pyneng --save-all            Сохранить на GitHub все измененные файлы в текущем каталоге
      pyneng --update              Обновить все задания и тесты в текущем каталоге
      pyneng --update --test-only  Обновить только тесты в текущем каталоге
      pyneng 1,2 --update          Обновить задания 1 и 2 и соответствующие тесты в текущем каталоге

    \b
    Запуск тестирования заданий, просмотр ответов, сдача на проверку
    \b
        pyneng              запустить все тесты для текущего раздела
        pyneng 1,2a,5       запустить тесты для заданий 1, 2a и 5
        pyneng 1,2*         запустить тесты для заданий 1, все задания 2 с буквами и без
        pyneng 1,3-5        запустить тесты для заданий 1, 3, 4, 5
        pyneng 1-5 -a       запустить тесты и записать ответы на задания,
                            которые прошли тесты, в файлы answer_task_x.py
        pyneng 1-5 -c       запустить тесты и сдать на проверку задания,
                            которые прошли тесты.
        pyneng 1-5 -c --all запустить тесты и сдать на проверку задания,
                            которые прошли тесты, но при этом загрузить на github все изменения
                            в текущем каталоге

    \b
    Флаг -d отключает подробный вывод pytest, который включен по умолчанию.
    Флаг -a записывает ответы в файлы answer_task_x.py, если тесты проходят.
    Флаг -c сдает на проверку задания (пишет комментарий на github)
    для которых прошли тесты.
    Для сдачи заданий на проверку надо сгенерировать токен github.
    Подробнее в инструкции: https://pyneng.natenka.io/docs/pyneng-prepare/
    """
    global DEFAULT_BRANCH
    if default_branch != "main":
        DEFAULT_BRANCH = default_branch
    token_error = red(
        "Для сдачи заданий на проверку надо сгенерировать токен github. "
        "Подробнее в инструкции: https://pyneng.natenka.io/docs/pyneng-prepare/"
    )
    if test_token:
        test_run_for_github_token()
        print(green("Проверка токена прошла успешно"))
        raise click.Abort()

    if save_all_to_github:
        save_changes_to_github()
        print(green("Все изменения в текущем каталоге сохранены на GitHub"))
        raise click.Abort()

    # после обработки CustomTasksType, получаем три списка файлов
    test_files, tasks_without_tests, task_files = tasks

    if update_tasks_tests and update_tests_only:
        update_tasks_and_tests(tasks_list=None, tests_list=test_files)
        print(green("Тесты успешно обновлены"))
        raise click.Abort()
    elif update_tasks_tests:
        update_tasks_and_tests(task_files, test_files)
        print(green("Задания и тесты успешно обновлены"))
        raise click.Abort()

    if not debug:
        sys.excepthook = exception_handler

    json_plugin = JSONReport()
    pytest_args_common = ["--json-report-file=none", "--disable-warnings"]

    if disable_verbose:
        pytest_args = [*pytest_args_common, "--tb=short"]
    else:
        pytest_args = [*pytest_args_common, "-vv", "--diff-width=120"]

    # если добавлен флаг -a или -c нет смысла выводить traceback,
    # так как скорее всего задания уже проверены предыдущими запусками.
    if answer or check:
        pytest_args = [*pytest_args_common, "--tb=no"]

    # запуск pytest
    pytest.main(test_files + pytest_args, plugins=[json_plugin])

    # получить результаты pytest в формате JSON
    # passed_tasks это задания у которых есть тесты и тесты прошли
    passed_tasks = parse_json_report(json_plugin.report)

    if passed_tasks or tasks_without_tests:
        # скопировать ответы в файлы answer_task_x.py
        if answer:
            copy_answers(passed_tasks)

        # сдать задания на проверку через github API
        if check:
            token = os.environ.get("GITHUB_TOKEN")
            if not token:
                raise PynengError(token_error)
            send_tasks_to_check(
                passed_tasks + tasks_without_tests,
                git_add_all=git_add_all_to_github,
                ignore_ssl_cert=ignore_ssl_cert,
            )

    # если добавлен флаг --all, надо сохранить все изменения на github
    if git_add_all_to_github:
        save_changes_to_github()


if __name__ == "__main__":
    cli()
