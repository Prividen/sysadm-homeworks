# Домашняя работа по занятию "4.3. Языки разметки JSON и YAML"

> 1. Мы выгрузили JSON, который получили через API запрос к нашему сервису:
...<br> 
> Нужно найти и исправить все ошибки, которые допускает наш сервис

```json
{
 "elements": [
  {
   "ip": 7175,
   "name": "first",
   "type": "server"
  },
  {
   "ip": "71.78.22.43",
   "name": "second",
   "type": "proxy"
  }
 ],
 "info": "Sample JSON output from our service\t"
}
```

---
> 2. В прошлый рабочий день мы создавали скрипт, позволяющий опрашивать веб-сервисы и получать их IP. К уже реализованному функционалу нам нужно добавить возможность записи JSON и YAML файлов, описывающих наши сервисы. Формат записи JSON по одному сервису: { "имя сервиса" : "его IP"}. Формат записи YAML по одному сервису: - имя сервиса: его IP. Если в момент исполнения скрипта меняется IP у сервиса - он должен так же поменяться в yml и json файле.

Получился список словарей, без родительского словаря.
```python
#!/usr/bin/env python3

import socket
import time
import json
import yaml

servers_to_check = [
    'drive.google.com',
    'mail.google.com',
    'google.com'
]

saved_ip_json_fn = "saved_ip.json"
saved_ip_yaml_fn = "saved_ip.yaml"

# sleep between checks
sleep_time = 10
saved_ip = {}

while True:
    resolved_ip = {}
    saved_ip_to_dump = []
    for host in servers_to_check:
        host_ip = socket.gethostbyname(host)
        print(f"<{host}> - <{host_ip}>")

        if host in saved_ip:
            if saved_ip[host] != host_ip:
                print(f"[ERROR] <{host}> IP mismatch: <{saved_ip[host]}> <{host_ip}>")

        saved_ip_to_dump.append({host: host_ip})
        resolved_ip[host] = host_ip
    saved_ip = resolved_ip

    with open(saved_ip_json_fn, "w") as json_fd:
        json_fd.write(json.dumps(saved_ip_to_dump))

    with open(saved_ip_yaml_fn, 'w') as yaml_fd:
        yaml_fd.write(yaml.dump(saved_ip_to_dump, explicit_start=True))

    time.sleep(sleep_time)
```
---
> Так как команды в нашей компании никак не могут прийти к единому мнению о том, какой формат разметки данных использовать: JSON или YAML, нам нужно реализовать парсер из одного формата в другой. Он должен уметь:
>   * Принимать на вход имя файла
>   * Проверять формат исходного файла. Если файл не json или yml - скрипт должен остановить свою работу
>   * Распознавать какой формат данных в файле. Считается, что файлы *.json и *.yml могут быть перепутаны
>   * Перекодировать данные из исходного формата во второй доступный (из JSON в YAML, из YAML в JSON)
>   * При обнаружении ошибки в исходном файле - указать в стандартном выводе строку с ошибкой синтаксиса и её номер
>   * Полученный файл должен иметь имя исходного файла, разница в наименовании обеспечивается разницей расширения файлов

[Конвертер](04-script-03-yaml-03.py) из JSON в YAML и обратно

