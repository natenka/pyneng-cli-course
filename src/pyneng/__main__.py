import os

import click
import pytest
from pytest_jsonreport.plugin import JSONReport

from pyneng import (
    DEFAULT_BRANCH,
    CustomTasksType,
    test_run_for_github_token,
    parse_json_report,
    copy_answers,
    PynengError,
    send_tasks_to_check,
    save_all_changes_to_github,
)


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
    save_all_to_github,
):
    """
    Запустить тесты для заданий TASKS. По умолчанию запустятся все тесты.

    Примеры запуска:

    \b
        pyneng --test-token проверить работу токена
        pyneng              запустить все тесты для текущего раздела
        pyneng 1,2a,5       запустить тесты для заданий 1, 2a и 5
        pyneng 1,2a-c,5     запустить тесты для заданий 1, 2a, 2b, 2c и 5
        pyneng 1,2*         запустить тесты для заданий 1, все задания 2 с буквами и без
        pyneng 1,3-5        запустить тесты для заданий 1, 3, 4, 5
        pyneng 1-5 -a       запустить тесты и записать ответы на задания,
                            которые прошли тесты, в файлы answer_task_x.py
        pyneng 1-5 -c       запустить тесты и сдать на проверку задания,
                            которые прошли тесты.
        pyneng -a -c        запустить все тесты, записать ответы на задания
                            и сдать на проверку задания, которые прошли тесты.
        pyneng 1-5 -c --all запустить тесты и сдать на проверку задания,
                            которые прошли тесты, но при этом загрузить на github все изменения
                            в текущем каталоге

    Флаг -d отключает подробный вывод pytest, который включен по умолчанию.
    Флаг -a записывает ответы в файлы answer_task_x.py, если тесты проходят.
    Флаг -c сдает на проверку задания (пишет комментарий на github)
    для которых прошли тесты.
    Для сдачи заданий на проверку надо сгенерировать токен github.
    Подробнее в инструкции: https://pyneng.github.io/docs/pyneng-prepare/
    """
    global DEFAULT_BRANCH
    if default_branch != "main":
        DEFAULT_BRANCH = default_branch
    token_error = red(
        "Для сдачи заданий на проверку надо сгенерировать токен github. "
        "Подробнее в инструкции: https://pyneng.github.io/docs/pyneng-prepare/"
    )
    if test_token:
        test_run_for_github_token()
        print(green("Проверка токена прошла успешно"))
        raise click.Abort()

    if not debug:
        sys.excepthook = exception_handler

    json_plugin = JSONReport()
    pytest_args_common = ["--json-report-file=none", "--disable-warnings"]

    if disable_verbose:
        pytest_args = [*pytest_args_common, "--tb=short"]
    else:
        pytest_args = [*pytest_args_common, "-vv"]

    # если добавлен флаг -a или -c нет смысла выводить traceback,
    # так как скорее всего задания уже проверены предыдущими запусками.
    if answer or check:
        pytest_args = [*pytest_args_common, "--tb=no"]

    # после обработки CustomTasksType, получаем два списка файлов
    test_files, tasks_without_tests = tasks

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
                passed_tasks + tasks_without_tests, git_add_all=save_all_to_github
            )

    # если добавлен флаг --all, надо сохранить все изменения на github
    if save_all_to_github:
        save_all_changes_to_github()


if __name__ == "__main__":
    cli()
