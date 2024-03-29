## pyneng

### Установка и запуск

Установить модуль

```
pip install pyneng-cli-course
```

После этого проверка заданий вызывается через утилиту pyneng в CLI.

### Этапы работы с заданиями

1. Выполнение заданий
2. Проверка, что задание отрабатывает как нужно ``python task_4_2.py`` или запуск скрипта в редакторе/IDE
3. Проверка заданий тестами ``pyneng 1-5``
4. Если тесты проходят, смотрим варианты решения ``pyneng 1-5 -a``
5. Сдача заданий на проверку ``pyneng 1-5 -c`` 


> Второй шаг очень важен, потому что на этом этапе намного проще найти ошибки в синтаксисе
> и подобные проблемы с работой скрипта, чем при запуске кода через тест на 3 этапе.

## Проверка заданий тестами

После выполнения задания, его надо проверить с помощью тестов.
Для запуска тестов, надо вызвать pyneng в каталоге заданий.
Например, если вы делаете 4 раздел заданий, надо находиться в каталоге exercises/04_data_structures/
и запустить pyneng одним из способов, в зависимости от того какие задания на проверять.

[Примеры вывода тестов с пояснениями](/docs/pyneng-output/)

Запуск проверки всех заданий текущего раздела:

```
pyneng
```

Запуск тестов для задания 4.1:

```
pyneng 1
```

Запуск тестов для заданий 4.1, 4.2, 4.3:

```
pyneng 1-3
```

Если есть задания с буквами, например, в 7 разделе, можно запускать так,
 чтобы запустить проверку для заданий 7.2a, 7.2b (надо находиться в каталоге 07_files):

```
pyneng 2a-b
```

или так, чтобы запустить все задания 7.2x с буквами и без:

```
pyneng 2*
```


## Получение ответов

Если задания проходят тесты, можно посмотреть варианты решения заданий.

Для этого к предыдущим вариантам команды надо добавить ``-a``.
Такой вызов значит запустить тесты для заданий 1 и 2 и скопировать ответы, если тесты прошли:

```
pyneng 1-2 -a
```

Тогда для указанных заданий запустятся тесты и для тех заданий из них,
которые прошли тесты, скопируются ответы в файлы answer_task_x.py в текущем каталоге.

Файлы ответов по умолчанию не добавляются на github.
Файлы ответов можно:

* удалять
* добавлять на github ``pyneng 1-3 -c --all`` (``--all`` добавляет все файлы в текущем
  каталоге и подкаталогах  ``git add .``, то есть добавит все файл)
* добавить в ``.gitignore``, чтобы они были локально, но не светились в репозитории.
  Для этого нужно добавить строку ``answer_task*`` в файл ``.gitignore``


Добавлять файлы в git есть смысл, если в них что-то писать. Например, комментарии
для себя по каким-то непонятным моментам.


## Сдача заданий на проверку

> Для сдачи задания на проверку, надо сгенерировать токен на Github.
> Как это сделать написано в инструкции [Подготовка к работе с заданиями](/docs/pyneng-prepare/)

После того как задания прошли тесты и вы посмотрели варианты решения заданий,
можно сдавать задания на проверку.

Для этого надо добавить ``-c`` к вызову pyneng:
Такой вызов значит запустить тесты для заданий 1 и 2 и сдать их на проверку, если тесты прошли:

```
pyneng 1-2 -c
```

Запустить тесты для всех заданий и сдать их на проверку, если тесты прошли:

```
pyneng -c
```

При добавлении ``-c`` pyneng делает git add файлам заданий, которые прошли тесты, делает commit,
и git push. После этого пишет комментарий на github, что задания такие-то сданы на проверку.
 
Запустить тесты и сдать на проверку задания,
которые прошли тесты, но при этом загрузить на github все изменения
в текущем каталоге:

```
pyneng 1-5 -c --all
```

## Загрузить все изменения в текущем каталоге на github, без привязки к тому проходят ли тесты

```
pyneng --save-all
```

Выполняет команды
```
git add .
git commit -m "Все изменения сохранены"
git push origin main
```

## Обновление разделов

В pyneng есть два варианта обновления: обновлять разделами или конкретные
задания/тесты.  При обновлении раздела, каталог раздела удаляется и копируется
новая версия. Это подходит только для тех разделов, которые вы еще не начинали
выполнять. Если надо обновить конкретное задание, лучше использовать обновление
конкретных заданий (рассматривается дальше).

Перед любым вариантом обновления желательно сохранить все локальные изменения
на github!

Для обновления разделов, надо перейти в каталог online-x-имя-фамилия/exercises/
и дать команду:

```
pyneng --update-chapters 12-25
```

В этом случае обновятся разделы 12-25. Также можно указывать один раздел:

```
pyneng --update-chapters 11
```

Или несколько через запятую

```
pyneng --update-chapters 12,15,17
```

## Обновление заданий и тестов

В заданиях и тестах встречаются неточности и чтобы их можно было исправить,
pyneng добавлена опция ``--update``.

Общая логика:

* задания и тесты копируются из репозитория https://github.com/pyneng/pyneng-course-tasks
* копируется весь файл задания, не только описание, поэтому файл перепишется
* перед выполнением --update, лучше созранить все изменения на github

Как работает --update

* если в репозитории есть несохраненные изменения
  * утилита предлагает их сохранить (сделает ``git add .``, ``git commit``, ``git push``)
* если несохраненных изменений нет, копируются указанные задания и тесты
* утилита предлагает сохранить изменения и показывает какие файлы изменены, но не какие именно сделаны изменения
* можно отказаться сохранять изменения и посмотреть изменения git diff

#### Варианты вызова

Обновить все задания и тесты раздела:

```
pyneng --update
```

Обновить все тесты раздела (только тесты, не задания):

```
pyneng --update --test-only
```

Обновить задания 1,2 и соответствующие тесты раздела

```
pyneng 1,2 --update
```

Если никаких обновлений нет, будет такой вывод

```
$ pyneng --update
#################### git pull
Already up-to-date.


Обновленные задания и тесты скопированы
Задания и тесты уже последней версии
Aborted!
```

В любой момент можно прервать обновление Ctrl-C.

Пример вывода с несохраненными изменениями и наличием обновлений
```
pyneng --update
ОБНОВЛЕНИЕ ТЕСТОВ И ЗАДАНИЕ ПЕРЕЗАПИШЕТ СОДЕРЖИМОЕ НЕСОХРАНЕННЫХ ФАЙЛОВ!
В текущем каталоге есть несохраненные изменения! Хотите их сохранить? [y/n]: y
#################### git add .
#################### git commit -m "Сохранение изменений перед обновлением заданий"
[main 0e8c1cb] Сохранение изменений перед обновлением заданий
 1 file changed, 1 insertion(+)

#################### git push origin main
To git@github.com:pyneng/online-14-natasha-samoylenko.git
   fa338c3..0e8c1cb  main -> main

Все изменения в текущем каталоге сохранены. Начинаем обновление...
#################### git pull
Already up-to-date.


Обновленные задания и тесты скопированы
Были обновлены такие файлы:
#################### git diff --stat
 exercises/04_data_structures/task_4_0.py |  0
 exercises/04_data_structures/task_4_1.py |  1 -
 exercises/04_data_structures/task_4_3.py |  3 ---
 3 files changed, 0 insertions(+), 4 deletions(-)


Это короткий diff, если вы хотите посмотреть все отличия подробно, нажмите n и дайте команду git diff.
Также при желании можно отменить внесенные изменения git checkout -- file (или git restore file).

Сохранить изменения и добавить на github? [y/n]: n
Задания и тесты успешно обновлены
Aborted!
```
