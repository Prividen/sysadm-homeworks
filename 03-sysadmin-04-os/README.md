# Домашняя работа по занятию "3.4. Операционные системы, лекция 2"

>1. На лекции мы познакомились с [node_exporter](https://github.com/prometheus/node_exporter/releases). В демонстрации его исполняемый файл запускался в background. Этого достаточно для демо, но не для настоящей production-системы, где процессы должны находиться под внешним управлением. Используя знания из лекции по systemd, создайте самостоятельно простой [unit-файл](https://www.freedesktop.org/software/systemd/man/systemd.service.html) для node_exporter:
>    * поместите его в автозагрузку,
>    * предусмотрите возможность добавления опций к запускаемому процессу через внешний файл (посмотрите, например, на `systemctl cat cron`),
>    * удостоверьтесь, что с помощью systemctl процесс корректно стартует, завершается, а после перезагрузки автоматически поднимается.

Вот наш unit-файл:
```
root@vagrant:~# cat /etc/systemd/system/node_exporter.service 
[Unit]
Description=Configurable modular Prometheus exporter for various node metrics.
After=network.target

[Service]
Type=simple
User=nobody
EnvironmentFile=-/etc/default/node_exporter
ExecStart=/usr/local/bin/node_exporter $OPTIONS
Restart=on-failure

[Install]
WantedBy=multi-user.target

```
И опция с немножечко параметров запуска во внешнем файле: 
```
root@vagrant:~# cat /etc/default/node_exporter
OPTIONS=--web.listen-address=":19100" \
--web.disable-exporter-metrics \
--log.level=warn
```
Старт, автозагрузка и перезагрузка:
```
root@vagrant:~# systemctl enable --now node_exporter
Created symlink /etc/systemd/system/multi-user.target.wants/node_exporter.service → /etc/systemd/system/node_exporter.service.
root@vagrant:~# systemctl status node_exporter
● node_exporter.service - Configurable modular Prometheus exporter for various node metrics.
     Loaded: loaded (/etc/systemd/system/node_exporter.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2021-03-25 01:22:34 UTC; 7s ago
   Main PID: 2005 (node_exporter)
      Tasks: 5 (limit: 19113)
     Memory: 4.6M
     CGroup: /system.slice/node_exporter.service
             └─2005 /usr/local/bin/node_exporter --web.listen-address=:19100 --web.disable-exporter-metrics --log.level=warn

Mar 25 01:22:34 vagrant systemd[1]: Started Configurable modular Prometheus exporter for various node metrics..
root@vagrant:~# reboot
Connection to 127.0.0.1 closed by remote host.
Connection to 127.0.0.1 closed.
mak@test-xu20:~/vagrant$ vagrant ssh
Welcome to Ubuntu 20.04.1 LTS (GNU/Linux 5.4.0-58-generic x86_64)
...
vagrant@vagrant:~$ curl localhost:19100/metrics 2>/dev/null |head
# HELP node_arp_entries ARP entries by device
# TYPE node_arp_entries gauge
node_arp_entries{device="eth0"} 1
# HELP node_boot_time_seconds Node boot time, in unixtime.
# TYPE node_boot_time_seconds gauge
node_boot_time_seconds 1.616635405e+09
# HELP node_context_switches_total Total number of context switches.
# TYPE node_context_switches_total counter
node_context_switches_total 47941
# HELP node_cooling_device_cur_state Current throttle state of the cooling device
```
---

>2. Приведите несколько опций, которые вы бы выбрали для базового мониторинга хоста по CPU, памяти, диску и сети.

* Для CPU наверное это семейство `node_cpu_seconds_total`, особенно интересные mode - 
user, system,  nice, iowait, idle. В совсем простом случае можно одним idle обойтись, как наиболее интегральным.
* Для памяти основная метрика - `node_memory_MemFree_bytes`, так же `node_memory_PageTables_bytes` 
(кажется это "used" в понимании `free`), `node_memory_Cached_bytes`, `node_memory_Buffers_bytes`, 
возможно `node_memory_Active_bytes`. Ну и `node_memory_MemTotal_bytes` для рассчёта %% использования. И для свопа,
 `node_memory_SwapTotal_bytes`, `node_memory_SwapCached_bytes`, `node_memory_SwapFree_bytes`.
* Для дисков я бы взял - `node_disk_io_time_seconds_total`, `node_disk_read_bytes_total`,  `node_disk_written_bytes_total`, и для файловых систем - `node_filesystem_size_bytes`, `node_filesystem_free_bytes`.
* В сети там чорт ногу сломит, но минимально можно наверное взять `node_network_receive_bytes_total`, `node_network_transmit_bytes_total`.



1. Установите в свою виртуальную машину [Netdata](https://github.com/netdata/netdata). Воспользуйтесь [готовыми пакетами](https://packagecloud.io/netdata/netdata/install) для установки (`sudo apt install -y netdata`). После успешной установки:
    * в конфигурационном файле `/etc/netdata/netdata.conf` в секции [web] замените значение с localhost на `bind to = 0.0.0.0`,
    * добавьте в Vagrantfile проброс порта Netdata на свой локальный компьютер и сделайте `vagrant reload`:

    ```bash
    config.vm.network "forwarded_port", guest: 19999, host: 19999
    ```

    После успешной перезагрузки в браузере *на своем ПК* (не в виртуальной машине) вы должны суметь зайти на `localhost:19999`. Ознакомьтесь с метриками, которые по умолчанию собираются Netdata и с комментариями, которые даны к этим метрикам.

1. Можно ли по выводу `dmesg` понять, осознает ли ОС, что загружена не на настоящем оборудовании, а на системе виртуализации?
1. Как настроен sysctl `fs.nr_open` на системе по-умолчанию? Узнайте, что означает этот параметр. Какой другой существующий лимит не позволит достичь такого числа (`ulimit --help`)?
1. Запустите любой долгоживущий процесс (не `ls`, который отработает мгновенно, а, например, `sleep 1h`) в отдельном неймспейсе процессов; покажите, что ваш процесс работает под PID 1 через `nsenter`. Для простоты работайте в данном задании под root (`sudo -i`). Под обычным пользователем требуются дополнительные опции (`--map-root-user`) и т.д.
1. Найдите информацию о том, что такое `:(){ :|:& };:`. Запустите эту команду в своей виртуальной машине Vagrant с Ubuntu 20.04 (**это важно, поведение в других ОС не проверялось**). Некоторое время все будет "плохо", после чего (минуты) – ОС должна стабилизироваться. Вызов `dmesg` расскажет, какой механизм помог автоматической стабилизации. Как настроен этот механизм по-умолчанию, и как изменить число процессов, которое можно создать в сессии?
