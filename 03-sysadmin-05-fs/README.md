# Домашняя работа по занятию "3.5. Файловые системы"

> 1. Узнайте о [sparse](https://ru.wikipedia.org/wiki/%D0%A0%D0%B0%D0%B7%D1%80%D0%B5%D0%B6%D1%91%D0%BD%D0%BD%D1%8B%D0%B9_%D1%84%D0%B0%D0%B9%D0%BB) (разряженных) файлах.

Раньше я умел их только `dd` делать, а теперь аж целыми тремя способами!

---
> 2. Могут ли файлы, являющиеся жесткой ссылкой на один объект, иметь разные права доступа и владельца? Почему?

Нет, не могут. Владельцы, права доступа, и прочие атрибуты-таймстампы хранятся в индексном дескрипторе файла, aka inode. Эта inode остаётся одной-единственной-уникальной для файла, вне зависимости от количества жестких ссылок, которые суть просто записи в разных директориях с ссылкой на эту самую inode. 

---
> 3. Сделайте `vagrant destroy` на имеющийся инстанс Ubuntu. Замените содержимое Vagrantfile...<br>
> ...<br>
> Данная конфигурация создаст новую виртуальную машину с двумя дополнительными неразмеченными дисками по 2.5 Гб.
```
root@vagrant:~# lsblk /dev/sd{b,c}
NAME MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sdb    8:16   0  2.5G  0 disk 
sdc    8:32   0  2.5G  0 disk 
```
---
> 4. Используя `fdisk`, разбейте первый диск на 2 раздела: 2 Гб, оставшееся пространство.
> 5. Используя `sfdisk`, перенесите данную таблицу разделов на второй диск.

```
Device     Boot   Start     End Sectors  Size Id Type
/dev/sdb1          2048 4196351 4194304    2G fd Linux raid autodetect
/dev/sdb2       4196352 5242879 1046528  511M fd Linux raid autodetect

Device     Boot   Start     End Sectors  Size Id Type
/dev/sdc1          2048 4196351 4194304    2G fd Linux raid autodetect
/dev/sdc2       4196352 5242879 1046528  511M fd Linux raid autodetect
```
---
> 6. Соберите `mdadm` RAID1 на паре разделов 2 Гб.
> 7. Соберите `mdadm` RAID0 на второй паре маленьких разделов.
```
root@vagrant:~# mdadm -C -e default -l 1 -n 2 /dev/md0 /dev/sd{b,c}1 
mdadm: array /dev/md0 started.
root@vagrant:~# mdadm -C -e default -l 0 -n 2 /dev/md1 /dev/sd{b,c}2
mdadm: array /dev/md1 started.
root@vagrant:~# cat /proc/mdstat 
Personalities : [linear] [multipath] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10] 
md1 : active raid0 sdc2[1] sdb2[0]
      1042432 blocks super 1.2 512k chunks
      
md0 : active raid1 sdc1[1] sdb1[0]
      2094080 blocks super 1.2 [2/2] [UU]
      
unused devices: <none>
```
---
> 8. Создайте 2 независимых PV на получившихся md-устройствах.
> 9. Создайте общую volume-group на этих двух PV.
```
root@vagrant:~# pvcreate /dev/md{0,1}
  Physical volume "/dev/md0" successfully created.
  Physical volume "/dev/md1" successfully created.
root@vagrant:~# vgcreate MyVG /dev/md{0,1}
  Volume group "MyVG" successfully created
```
---
> 10. Создайте LV размером 100 Мб, указав его расположение на PV с RAID0.
```
root@vagrant:~# lvcreate -n MyLV0 -L 100MiB MyVG /dev/md1
  Logical volume "MyLV0" created.
root@vagrant:~# pvdisplay /dev/md1 |grep PE
  PE Size               4.00 MiB
  Total PE              254
  Free PE               229
  Allocated PE          25
```
---
> 11. Создайте `mkfs.ext4` ФС на получившемся LV.
> 12. Смонтируйте этот раздел в любую директорию, например, `/tmp/new`.
> 13. Поместите туда тестовый файл, например `wget https://mirror.yandex.ru/ubuntu/ls-lR.gz -O /tmp/new/test.gz`.
> 14. Прикрепите вывод `lsblk`.
```
root@vagrant:~# lsblk -f
NAME                 FSTYPE            LABEL     UUID                                   FSAVAIL FSUSE% MOUNTPOINT
sda                                                                                                    
├─sda1               vfat                        5A33-EBB5                                 511M     0% /boot/efi
├─sda2                                                                                                 
└─sda5               LVM2_member                 OCbATH-NO0a-4yCv-lVyW-UOYQ-uFJm-DPdN8c                
  ├─vgvagrant-root   ext4                        64ad40d3-1c01-44d8-8d97-711d728fb3fb     56.5G     3% /
  └─vgvagrant-swap_1 swap                        7aa737aa-768b-4479-800b-ac47ec04e71f                  [SWAP]
sdb                                                                                                    
├─sdb1               linux_raid_member vagrant:0 c57a2153-eb34-2bd5-194a-74658ce61f1d                  
│ └─md0              LVM2_member                 nQQMbs-4FQj-qxD1-ndmW-4bcy-mWGW-mVrJES                
└─sdb2               linux_raid_member vagrant:1 b56972cd-3596-3e2e-5871-1d3d2837d417                  
  └─md1              LVM2_member                 CimqfH-wE04-4AKB-eMfk-IcxE-WVFJ-rvsAWq                
    └─MyVG-MyLV0     ext4                        c740048c-a41a-4306-b8f3-60d4e46c867c     66.6M    21% /mnt
sdc                                                                                                    
├─sdc1               linux_raid_member vagrant:0 c57a2153-eb34-2bd5-194a-74658ce61f1d                  
│ └─md0              LVM2_member                 nQQMbs-4FQj-qxD1-ndmW-4bcy-mWGW-mVrJES                
└─sdc2               linux_raid_member vagrant:1 b56972cd-3596-3e2e-5871-1d3d2837d417                  
  └─md1              LVM2_member                 CimqfH-wE04-4AKB-eMfk-IcxE-WVFJ-rvsAWq                
    └─MyVG-MyLV0     ext4                        c740048c-a41a-4306-b8f3-60d4e46c867c     66.6M    21% /mnt
```
---
> 15. Протестируйте целостность файла:
```
root@vagrant:~# gzip -t /mnt/test.gz && echo "good!"
good!
```
---
> 16. Используя pvmove, переместите содержимое PV с RAID0 на RAID1.
```
root@vagrant:~# pvmove /dev/md1
  /dev/md1: Moved: 32.00%
  /dev/md1: Moved: 100.00%
oot@vagrant:~# pvdisplay /dev/md0 |grep PE
  PE Size               4.00 MiB
  Total PE              511
  Free PE               486
  Allocated PE          25
root@vagrant:~# pvdisplay /dev/md1 |grep PE
  PE Size               4.00 MiB
  Total PE              254
  Free PE               254
  Allocated PE          0
```
---
> 17. Сделайте `--fail` на устройство в вашем RAID1 md.
> 18. Подтвердите выводом `dmesg`, что RAID1 работает в деградированном состоянии.
```
root@vagrant:~# mdadm /dev/md0 --fail /dev/sdc1
mdadm: set /dev/sdc1 faulty in /dev/md0
root@vagrant:~# dmesg |tail -2
[ 5212.744566] md/raid1:md0: Disk failure on sdc1, disabling device.
               md/raid1:md0: Operation continuing on 1 devices.
root@vagrant:~# cat /proc/mdstat |grep -A1 md0
md0 : active raid1 sdc1[1](F) sdb1[0]
      2094080 blocks super 1.2 [2/1] [U_]
```
---
> 19. Протестируйте целостность файла, несмотря на "сбойный" диск он должен продолжать быть доступен:
```
root@vagrant:~# gzip -t /mnt/test.gz && echo "Still be good!"
Still be good!
```
---
> 20. Погасите тестовый хост, `vagrant destroy`.
```
mak@test-xu20:~/vagrant$ vagrant destroy -f
==> default: Forcing shutdown of VM...
==> default: Destroying VM and associated drives...
```
