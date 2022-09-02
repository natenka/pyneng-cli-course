import sys
import subprocess
from platform import system as system_name
import re
import os
from pprint import pprint
from collections import defaultdict
import tempfile
import json
import pathlib
from getpass import getpass
import stat
import shutil
from datetime import datetime, timedelta
from glob import glob


import click
import yaml
import pytest
from pytest_jsonreport.plugin import JSONReport
import requests
import github

from pyneng import ANSWERS_URL, TASKS_URL, DEFAULT_BRANCH, TASK_DIRS, DB_TASK_DIRS


class PynengError(Exception):
    """
    Ошибка в использовании/работе скрипта pyneng
    """


def red(msg):
    return click.style(msg, fg="red")


def green(msg):
    return click.style(msg, fg="green")


def exception_handler(exception_type, exception, traceback):
    """
    sys.excepthook для отключения traceback по умолчанию
    """
    print(f"\n{exception_type.__name__}: {exception}\n")


class CustomTasksType(click.ParamType):
    """
    Класс создает новый тип для click и преобразует
    допустимые варианты строк заданий в отдельные файлы тестов.

    Кроме того проверяет есть ли такой файл в текущем каталоге
    и оставляет только те, что есть.
    """

    name = "CustomTasksType"

    def convert(self, value, param, ctx):
        # for some reason click can call this method with parsed args
        # this allowes to return parsed value as is
        if isinstance(value, tuple):
            return value

        regex = (
            r"(?P<all>all)|"
            r"(?P<number_star>\d\*)|"
            r"(?P<letters_range>\d[a-i]-[a-i])|"
            r"(?P<numbers_range>\d-\d)|"
            r"(?P<single_task>\d[a-i]?)"
        )
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

        tasks_list = re.split(r"[ ,]+", value)
        current_chapter = current_chapter_id()
        test_files = []
        task_files = []
        for task in tasks_list:
            match = re.fullmatch(regex, task)
            if match:
                if task == "all":
                    test_files = sorted(glob(f"test_task_{current_chapter}_*.py"))
                    task_files = glob(f"task_{current_chapter}_*.py")
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
        return sorted(test_files), sorted(tasks_without_tests)


def git_push():
    """
    Функция вызывает git push для Windows
    """
    command = f"git push origin {DEFAULT_BRANCH}"
    print("#" * 20, command)
    result = subprocess.run(command, shell=True)


def call_command(command, verbose=True, return_stdout=False, return_stderr=False):
    """
    Функция вызывает указанную command через subprocess
    и выводит stdout и stderr, если флаг verbose=True.
    """
    result = subprocess.run(
        command,
        shell=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    std = result.stdout
    stderr = result.stderr
    if return_stdout:
        return std
    if return_stderr:
        return result.returncode, stderr
    if verbose:
        print("#" * 20, command)
        if std:
            print(std)
        if stderr:
            print(stderr)
    return result.returncode


def post_comment_to_last_commit(msg, repo, delta_days=60):
    """
    Написать комментарий о сдаче заданий в последнем коммите.
    Комментарий пишется через Github API.

    Для работы функции должен быть настроен git.
    Функция пытается определить имя пользователя git из вывода git config --list,
    Если это не получается, запрашивает имя пользователя.

    Пароль берется из переменной окружения GITHUB_PASS или запрашивается.
    """
    token = os.environ.get("GITHUB_TOKEN")
    since = datetime.now() - timedelta(days=delta_days)
    repo_name = f"pyneng/{repo}"

    try:
        g = github.Github(token)
        repo_obj = g.get_repo(repo_name)
    except github.GithubException:
        raise PynengError(
            red("Аутентификация по токену не прошла. Задание не сдано на проверку")
        )
    else:
        commits = repo_obj.get_commits(since=since)

        try:
            last = commits[0]
        except IndexError:
            print(f"За указанный период времени {delta_days} дней не найдено коммитов")
        else:
            last.create_comment(msg)
            return last


def get_repo(search_pattern=r"online-\d+-\w+-\w+"):
    git_remote = call_command("git remote -v", return_stdout=True)
    repo_match = re.search(search_pattern, git_remote)
    if repo_match:
        repo = repo_match.group()
        return repo
    else:
        raise PynengError(
            red(
                "Не найден репозиторий online-x-имя-фамилия. "
                "pyneng надо вызывать в репозитории подготовленном для курса."
            )
        )


def send_tasks_to_check(passed_tasks, git_add_all=False):
    """
    Функция отбирает все задания, которые прошли
    тесты при вызове pyneng, делает git add для файлов заданий,
    git commit с сообщением какие задания сделаны
    и git push для добавления изменений на Github.
    После этого к этому коммиту добавляется сообщение о том,
    что задания сдаются на проверку с помощью функции post_comment_to_last_commit.
    """
    ok_tasks = [
        re.sub(r".*(task_\d+_\w+.py)", r"\1", filename) for filename in passed_tasks
    ]
    tasks_num_only = sorted(
        [task.replace("task_", "").replace(".py", "") for task in ok_tasks]
    )
    message = f"Сделаны задания {' '.join(tasks_num_only)}"

    for task in ok_tasks:
        call_command(f"git add {task}")
        # добавление шаблонов для заданий jinja, textfsm
        if "20" in task or "21" in task:
            call_command("git add templates")
        elif "25" in task:
            call_command("git add .")
    if git_add_all:
        call_command("git add .")
    call_command(f'git commit -m "{message}"')
    windows = True if system_name().lower() == "windows" else False

    if windows:
        git_push()
    else:
        call_command(f"git push origin {DEFAULT_BRANCH}")

    repo = get_repo()
    last = post_comment_to_last_commit(message, repo)
    commit_number = re.search(r'"(\w+)"', str(last)).group(1)
    print(
        green(
            f"Задание успешно сдано на проверку. Комментарий о сдаче задания "
            f"можно посмотреть по ссылке https://github.com/pyneng/{repo}/commit/{commit_number}"
        )
    )


def save_all_changes_to_github():
    status = call_command("git status -s", return_stdout=True)
    if not status:
        return
    message = "Все изменения сохранены"
    call_command("git add .")
    call_command(f'git commit -m "{message}"')
    windows = True if system_name().lower() == "windows" else False

    if windows:
        git_push()
    else:
        call_command(f"git push origin {DEFAULT_BRANCH}")


def test_run_for_github_token():
    """
    Функция добавляет тестовое сообщение к последнему за 2 недели коммиту
    """
    message = "Проверка работы токена прошла успешно"
    repo = get_repo()
    last = post_comment_to_last_commit(message, repo)
    commit_number = re.search(r'"(\w+)"', str(last)).group(1)
    print(
        green(
            f"Комментарий можно посмотреть по ссылке "
            f"https://github.com/pyneng/{repo}/commit/{commit_number}"
        )
    )


def current_chapter_id():
    """
    Функция возвращает номер текущего раздела, где вызывается pyneng.
    """
    current_chapter_name = current_dir_name()
    if current_chapter_name in DB_TASK_DIRS:
        current_chapter_name = TASK_DIRS[-1]
    current_chapter = int(current_chapter_name.split("_")[0])
    return current_chapter


def current_dir_name():
    pth = str(pathlib.Path().absolute())
    current_chapter_name = os.path.split(pth)[-1]
    return current_chapter_name


def parse_json_report(report):
    """
    Отбирает нужные части из отчета запуска pytest в формате JSON.
    Возвращает список тестов, которые прошли.
    """
    if report and report["summary"]["total"] != 0:
        all_tests = defaultdict(list)
        summary = report["summary"]

        test_names = [test["nodeid"] for test in report["collectors"][0]["result"]]
        for test in report["tests"]:
            name = test["nodeid"].split("::")[0]
            all_tests[name].append(test["outcome"] == "passed")
        all_passed_tasks = [name for name, outcome in all_tests.items() if all(outcome)]
        return all_passed_tasks
    else:
        return []


def copy_answers(passed_tasks):
    """
    Функция клонирует репозиторий с ответами и копирует ответы для заданий,
    которые прошли тесты.
    """
    pth = str(pathlib.Path().absolute())
    current_chapter_name = os.path.split(pth)[-1]
    current_chapter_number = int(current_chapter_name.split("_")[0])

    homedir = pathlib.Path.home()
    os.chdir(homedir)
    if os.path.exists("pyneng-answers"):
        shutil.rmtree("pyneng-answers", onerror=remove_readonly)
    returncode, stderr = call_command(
        "git clone https://github.com/natenka/pyneng-answers",
        verbose=False,
        return_stderr=True,
    )
    if returncode == 0:
        os.chdir(f"pyneng-answers/answers/{current_chapter_name}")
        copy_answer_files(passed_tasks, pth)
        print(
            green(
                "\nОтветы на задания, которые прошли тесты "
                "скопированы в файлы answer_task_x.py\n"
            )
        )
        os.chdir(homedir)
        shutil.rmtree("pyneng-answers", onerror=remove_readonly)
    else:
        if "could not resolve host" in stderr.lower():
            raise PynengError(
                red(
                    "Не получилось скопировать ответы. Возможно нет доступа в интернет?"
                )
            )
        else:
            raise PynengError(red(f"Не получилось скопировать ответы. {stderr}"))
    os.chdir(pth)


def remove_readonly(func, path, _):
    """
    Вспомогательная функция для Windows, которая позволяет удалять
    read only файлы из каталога .git
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def copy_answer_files(passed_tasks, pth):
    """
    Функция копирует ответы для указанных заданий.
    """
    for test_file in passed_tasks:
        task_name = test_file.replace("test_", "")
        task_name = re.search(r"task_\w+\.py", task_name).group()
        answer_name = test_file.replace("test_", "answer_")
        answer_name = re.search(r"answer_task_\w+\.py", answer_name).group()
        if not os.path.exists(f"{pth}/{answer_name}"):
            # call_command(
            #    f"cp {task_name} {pth}/{answer_name}",
            #    verbose=False,
            # )
            shutil.copy2(task_name, f"{pth}/{answer_name}")
