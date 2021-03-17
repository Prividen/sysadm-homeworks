# Домашнее задание к занятию "3.3. Операционные системы, лекция 1"

> Какой системный вызов делает команда `cd`? В прошлом ДЗ мы выяснили, что `cd` не является самостоятельной  программой, это `shell builtin`, поэтому запустить `strace` непосредственно на `cd` не получится. Тем не менее, вы можете запустить `strace` на `/bin/bash -c 'cd /tmp'`. В этом случае вы увидите полный список системных вызовов, которые делает сам `bash` при старте. Вам нужно найти тот единственный, который относится именно к `cd`.

Вызов `chdir`.  
***
>    Используя `strace` выясните, где находится база данных `file` на основании которой она делает свои догадки.

`/usr/share/misc/magic.mgc`<br>
Так же, пытаются прочесться `/etc/magic.mgc` и `~/.magic.mgc`
***
> Предположим, приложение пишет лог в текстовый файл. Этот файл оказался удален (deleted в lsof), однако возможности сигналом сказать приложению переоткрыть файлы или просто перезапустить приложение – нет. Так как приложение продолжает писать в удаленный файл, место на диске постепенно заканчивается. Основываясь на знаниях о перенаправлении потоков предложите способ обнуления открытого удаленного файла (чтобы освободить место на файловой системе).

Ой, как интересно. Попробуем смоделировать:
* сделаем маленькую файловую систему
```
# mount -t tmpfs -o size=1M tmpfs /tmp/test
# df -B 1  /tmp/test/
Filesystem     1B-blocks  Used Available Use% Mounted on
tmpfs            1048576     0   1048576   0% /tmp/test
```
* в соседней консоли запустим `cat`, чтобы записала большой файл и подождала:
```
# tail -n +1 -f /usr/share/doc/xterm/xterm.log.html | cat > /tmp/test/file-to-be-deleted
```
* посмотрим сколько и чем отъелось места:
```
# df -B 1  /tmp/test/
Filesystem     1B-blocks   Used Available Use% Mounted on
tmpfs            1048576 577536    471040  56% /tmp/test

# lsof -p $(pidof cat)
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF    NODE NAME
cat     48396 root  cwd    DIR    8,5     4096 6684673 /root
cat     48396 root  rtd    DIR    8,5     4096       2 /
cat     48396 root  txt    REG    8,5    43416 2752671 /usr/bin/cat
cat     48396 root  mem    REG    8,5 16287648 2757963 /usr/lib/locale/locale-archive
cat     48396 root  mem    REG    8,5  2029224 2758947 /usr/lib/x86_64-linux-gnu/libc-2.31.so
cat     48396 root  mem    REG    8,5   191472 2758681 /usr/lib/x86_64-linux-gnu/ld-2.31.so
cat     48396 root    0r  FIFO   0,12      0t0  278436 pipe
cat     48396 root    1w   REG   0,55   574685       3 /tmp/test/file-to-be-deleted
cat     48396 root    2u   CHR  136,0      0t0       3 /dev/pts/0

```
* Удалим файл, проверим снова, чтобы убедиться, что наше место это не спасло. Напротив имени файла в выводе `lsof` появилась пометка `(deleted)`, но размер его не изменился.:
```
# rm -f /tmp/test/file-to-be-deleted

# df -B 1  /tmp/test/
Filesystem     1B-blocks   Used Available Use% Mounted on
tmpfs            1048576 577536    471040  56% /tmp/test

# lsof -p $(pidof cat)
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF    NODE NAME
cat     48396 root  cwd    DIR    8,5     4096 6684673 /root
cat     48396 root  rtd    DIR    8,5     4096       2 /
cat     48396 root  txt    REG    8,5    43416 2752671 /usr/bin/cat
cat     48396 root  mem    REG    8,5 16287648 2757963 /usr/lib/locale/locale-archive
cat     48396 root  mem    REG    8,5  2029224 2758947 /usr/lib/x86_64-linux-gnu/libc-2.31.so
cat     48396 root  mem    REG    8,5   191472 2758681 /usr/lib/x86_64-linux-gnu/ld-2.31.so
cat     48396 root    0r  FIFO   0,12      0t0  278436 pipe
cat     48396 root    1w   REG   0,55   574685       3 /tmp/test/file-to-be-deleted (deleted)
cat     48396 root    2u   CHR  136,0      0t0       3 /dev/pts/0

```
* А теперь магия. Выведем в этот файл, всё ещё доступный по дескриптору (#1, stdout для cat), всё-всё содержимое `/dev/null`. И проверим снова:
```
# cat /dev/null >/proc/$(pidof cat)/fd/1

# df -B 1  /tmp/test/
Filesystem     1B-blocks  Used Available Use% Mounted on
tmpfs            1048576     0   1048576   0% /tmp/test

# lsof -p $(pidof cat)
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF    NODE NAME
cat     48396 root  cwd    DIR    8,5     4096 6684673 /root
cat     48396 root  rtd    DIR    8,5     4096       2 /
cat     48396 root  txt    REG    8,5    43416 2752671 /usr/bin/cat
cat     48396 root  mem    REG    8,5 16287648 2757963 /usr/lib/locale/locale-archive
cat     48396 root  mem    REG    8,5  2029224 2758947 /usr/lib/x86_64-linux-gnu/libc-2.31.so
cat     48396 root  mem    REG    8,5   191472 2758681 /usr/lib/x86_64-linux-gnu/ld-2.31.so
cat     48396 root    0r  FIFO   0,12      0t0  278436 pipe
cat     48396 root    1w   REG   0,55        0       3 /tmp/test/file-to-be-deleted (deleted)
cat     48396 root    2u   CHR  136,0      0t0       3 /dev/pts/0
```
Место на диске освободилось, недо-удалённый файл теперь нулевого размера.
***
> Занимают ли зомби-процессы какие-то ресурсы в ОС (CPU, RAM, IO)?

Вопреки утверждаемому в лекции, никаких системных ресурсов, кроме записи в таблице процессов (PID), они не расходуют. Ни CPU, ни памяти, ни операций ввода-вывода.
***
> В iovisor BCC есть утилита `opensnoop`: На какие файлы вы увидели вызовы группы `open` за первую секунду работы утилиты?

Каждый раз разные. Например, такие:
```
# opensnoop-bpfcc -d 1
PID    COMM               FD ERR PATH
809    irqbalance          6   0 /proc/interrupts
809    irqbalance          6   0 /proc/stat
809    irqbalance          6   0 /proc/irq/67/smp_affinity
809    irqbalance         -1   2 /proc/irq/34/smp_affinity
809    irqbalance          6   0 /proc/irq/65/smp_affinity
809    irqbalance         -1   2 /proc/irq/25/smp_affinity
809    irqbalance          6   0 /proc/irq/81/smp_affinity
809    irqbalance          6   0 /proc/irq/62/smp_affinity
809    irqbalance          6   0 /proc/irq/79/smp_affinity
809    irqbalance          6   0 /proc/irq/77/smp_affinity
809    irqbalance          6   0 /proc/irq/70/smp_affinity
809    irqbalance         -1   2 /proc/irq/31/smp_affinity
809    irqbalance          6   0 /proc/irq/74/smp_affinity
809    irqbalance          6   0 /proc/irq/68/smp_affinity
809    irqbalance         -1   2 /proc/irq/30/smp_affinity
809    irqbalance          6   0 /proc/irq/66/smp_affinity
809    irqbalance         -1   2 /proc/irq/26/smp_affinity
809    irqbalance          6   0 /proc/irq/82/smp_affinity
809    irqbalance          6   0 /proc/irq/64/smp_affinity
809    irqbalance          6   0 /proc/irq/80/smp_affinity
809    irqbalance         -1   2 /proc/irq/36/smp_affinity
809    irqbalance         -1   2 /proc/irq/32/smp_affinity
809    irqbalance          6   0 /proc/irq/78/smp_affinity
809    irqbalance         -1   2 /proc/irq/28/smp_affinity
809    irqbalance          6   0 /proc/irq/76/smp_affinity
809    irqbalance          6   0 /proc/irq/69/smp_affinity
493    systemd-journal    53   0 /proc/2319/status
493    systemd-journal    53   0 /proc/2319/status
493    systemd-journal    53   0 /proc/2319/comm
```
***
> Какой системный вызов использует `uname -a`? 

Одноимённый вызов `uname`.

> Приведите цитату из man по этому системному вызову, где описывается альтернативное местоположение в `/proc`, где можно узнать версию ядра и релиз ОС.

"Part of the utsname information is also accessible via /proc/sys/kernel/{ostype, hostname, osrelease, version,domainname}."
***

> Чем отличается последовательность команд через `;` и через `&&` в bash? 
   
Если команды разделены точкой с запятой, они обе выполнятся в любом случае. Если они разделены `&&`, то вторая команда выполнится, только если первая вернёт нулевой код возврата (нет ошибки).

> Есть ли смысл использовать в bash `&&`, если применить `set -e`?

В режиме `-e` шелл завершится только при ненулевом коде возврата простой команды. Если ошибочно завершится одна из команд, разделённых `&&` (кроме последней), то выхода из шелла не произойдёт. Так что да, смысл есть.
***

> Из каких опций состоит режим bash `set -euxo pipefail`

* -e (выход из шелла/скрипта, если одна из команд вернёт ненулевой код возврата (ошибку));
* -u (выход из скрипта по ошибке при попытке использования несуществующей переменной или подстановки несуществующего параметра)
* -x (вывод всех выполняемых команд)
* -o pipefail (если одна из команд в цепочке пайпов завершится аварийно, то вся цепочка тоже завершится с ошибкой и вернёт код возврата этой команды)

> почему его хорошо было бы использовать в сценариях?

`-x` хорошо использовать для отладки, при сомнении в последовательности выполняемых команд, текущего значения их аргументов, etc. Опции `-euo pipefail` позволят избежать скрытых трудноуловимых ошибок, сделав таковые явными и отчётливо заметными. 
***

> Используя `-o stat` для `ps`, определите, какой наиболее часто встречающийся статус у процессов в системе. В `man ps` ознакомьтесь (`/PROCESS STATE CODES`) что значат дополнительные к основной заглавной буквы статуса процессов. Его можно не учитывать при расчете (считать S, Ss или Ssl равнозначными).
```
# ps ax -o stat |cut -c1 |sort |uniq -c
      4 R
    595 S
      1 Z
```
Четверо работают, остальные чего-то ждут и спят. Но их можно разбудить событием. И одна зомбичка!
