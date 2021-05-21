# Домашняя работа по занятию "4.2. Использование Python для решения типовых DevOps задач"

> 1. Есть скрипт:
> ...
> * Какое значение будет присвоено переменной c?

Никакое, скрипт вылетет с ошибкой, от ужаса, что складывают число со строкой.

> * Как получить для переменной c значение 12?

Нужно преобразовать `a` к строке и сложить строку со строкой:
```python
>>> c = str(a) + b
>>> c
'12'
```
> * Как получить для переменной c значение 3?

Нужно преобразовать `b` к целому и сложить два числовых значения:
```python
>>> c = a + int(b)
>>> c
3
```

---
> 2. Мы устроились на работу в компанию, где раньше уже был DevOps Engineer. Он написал скрипт, позволяющий узнать, какие файлы модифицированы в репозитории, относительно локальных изменений. Этим скриптом недовольно начальство, потому что в его выводе есть не все изменённые файлы, а также непонятен полный путь к директории, где они находятся. Как можно доработать скрипт ниже, чтобы он исполнял требования вашего руководителя?

Не совсем понятны непонятки начальства относительно полного пути, но предположим, что скрипт 
предназначен для проверки репозитария `~/netology/sysadm-homeworks` у любого пользователя, который его вызовет. А на мы на радость начальству выведем полный путь, с которым будем работать: 

```python
#!/usr/bin/env python3

import os
from pathlib import Path


def path_normalization(rel_path):
    return os.path.abspath(rel_path.replace('~', str(Path.home())))


git_relative_path = "~/netology/sysadm-homeworks"
git_full_path = path_normalization(git_relative_path)

print(f"Checking for modified GIT files in {git_full_path} directory:")

bash_command = [f"cd {git_full_path}", "git status"]
result_os = os.popen(' && '.join(bash_command)).read()

for result in result_os.split('\n'):
    if result.find('modified') != -1:
        prepare_result = result.replace('\tmodified:   ', '')
        print(prepare_result)

```

---
> 3. Доработать скрипт выше так, чтобы он мог проверять не только локальный репозиторий в текущей директории, а также умел воспринимать путь к репозиторию, который мы передаём как входной параметр. Мы точно знаем, что начальство коварное и будет проверять работу этого скрипта в директориях, которые не являются локальными репозиториями.
```python
#!/usr/bin/env python3

import os
import sys
from pathlib import Path


def path_normalization(rel_path):
    return os.path.abspath(rel_path.replace('~', str(Path.home())))


if len(sys.argv) > 1:
    git_relative_path = sys.argv[1]
else:
    git_relative_path = '.'

git_full_path = path_normalization(git_relative_path)

if not os.path.isdir(git_full_path):
    print(f"Directory {git_full_path} doesn't exist", file=sys.stderr)
    exit(1)

if not os.path.isdir(git_full_path + "/.git"):
    print(f"Directory {git_full_path} is not a GIT repository", file=sys.stderr)
    exit(1)

print(f"Checking for modified GIT files in {git_full_path} directory:")

bash_command = [f"cd {git_full_path}", "git status"]
result_os = os.popen(' && '.join(bash_command)).read()

for result in result_os.split('\n'):
    if result.find('modified') != -1:
        prepare_result = result.replace('\tmodified:   ', '')
        print(prepare_result)
```

---
> 4. Наша команда разрабатывает несколько веб-сервисов, доступных по http. Мы точно знаем, что на их стенде нет никакой балансировки, кластеризации, за DNS прячется конкретный IP сервера, где установлен сервис. Проблема в том, что отдел, занимающийся нашей инфраструктурой очень часто меняет нам сервера, поэтому IP меняются примерно раз в неделю, при этом сервисы сохраняют за собой DNS имена. Это бы совсем никого не беспокоило, если бы несколько раз сервера не уезжали в такой сегмент сети нашей компании, который недоступен для разработчиков. Мы хотим написать скрипт, который опрашивает веб-сервисы, получает их IP, выводит информацию в стандартный вывод в виде: <URL сервиса> - <его IP>. Также, должна быть реализована возможность проверки текущего IP сервиса c его IP из предыдущей проверки. Если проверка будет провалена - оповестить об этом в стандартный вывод сообщением: [ERROR] <URL сервиса> IP mismatch: <старый IP> <Новый IP>. Будем считать, что наша разработка реализовала сервисы: drive.google.com, mail.google.com, google.com.

Сначала было я решил, что скрипт будут вызывать из крона, и сделал такой вариант с сохранением в файлик:
```python
#!/usr/bin/env python3

import os
import socket
import json

servers_to_check = [
    'drive.google.com',
    'mail.google.com',
    'google.com'
]

saved_ip_filename = "saved_ip.json"
saved_ip = {}
resolved_ip = {}

if os.path.exists(saved_ip_filename):
    saved_ip_fh = open(saved_ip_filename, "r")
    saved_ip = json.load(saved_ip_fh)
    saved_ip_fh.close()

for host in servers_to_check:
    host_ip = socket.gethostbyname(host)
    print(f"{host} - {host_ip}")

    if host in saved_ip:
        if saved_ip[host] != host_ip:
            print(f"[ERROR] {host} IP mismatch: {saved_ip[host]} {host_ip}")

    resolved_ip[host] = host_ip

saved_ip_fh = open(saved_ip_filename, "w")
json.dump(resolved_ip, saved_ip_fh)
saved_ip_fh.close()
```
Но, в свете следующего домашнего задания по json/yaml подумалось, что может быть тут этот скрипт должен работать демоном и делать проверки в бесконечном цикле... тогда упростим:  
```python
#!/usr/bin/env python3

import socket
import time

servers_to_check = [
    'drive.google.com',
    'mail.google.com',
    'google.com'
]

# sleep between checks
sleep_time = 10
saved_ip = {}

while True:
    resolved_ip = {}
    for host in servers_to_check:
        host_ip = socket.gethostbyname(host)
        print(f"<{host}> - <{host_ip}>")

        if host in saved_ip:
            if saved_ip[host] != host_ip:
                print(f"[ERROR] <{host}> IP mismatch: <{saved_ip[host]}> <{host_ip}>")

        resolved_ip[host] = host_ip
    saved_ip = resolved_ip
    time.sleep(sleep_time)
```

---
> Так получилось, что мы очень часто вносим правки в конфигурацию своей системы прямо на сервере. Но так как вся наша команда разработки держит файлы конфигурации в github и пользуется gitflow, то нам приходится каждый раз переносить архив с нашими изменениями с сервера на наш локальный компьютер, формировать новую ветку, коммитить в неё изменения, создавать pull request (PR) и только после выполнения Merge мы наконец можем официально подтвердить, что новая конфигурация применена. Мы хотим максимально автоматизировать всю цепочку действий. Для этого нам нужно написать скрипт, который будет в директории с локальным репозиторием обращаться по API к github, создавать PR для вливания текущей выбранной ветки в master с сообщением, которое мы вписываем в первый параметр при обращении к py-файлу (сообщение не может быть пустым). При желании, можно добавить к указанному функционалу создание новой ветки, commit и push в неё изменений конфигурации. С директорией локального репозитория можно делать всё, что угодно. Также, принимаем во внимание, что Merge Conflict у нас отсутствуют и их точно не будет при push, как в свою ветку, так и при слиянии в master. Важно получить конечный результат с созданным PR, в котором применяются наши изменения. 

Получившийся монстр Франкенштейна из кусков гугля и стековерфлоу заслуживает [отдельного файла](04-script-02-py-05.py) в репозитарии. Его можно улучшать бесконечно, дописывать проверки и реализовывать какие-нибудь классы, наверняка остались невыловленные ошибки. Ну пока так.

Из недореализованного:
- нет заботы об удалении рабочих веток в GitHub repo
- нет нормальной обработки отклонённых PR, несмерженный коммит попадёт в следующий PR
- права и владельцы конфигов не сохраняются

Ну и история получается кривоватая:
```
119491f Merge pull request #5 from Prividen/home-etc-testconf-1621611441
5fa0c3c (origin/home-etc-testconf-1621611441) Another commit msg
448308f Merge pull request #4 from Prividen/home-etc-testconf-1621611173
0feace3 (origin/home-etc-testconf-1621611173) My commit msg
```