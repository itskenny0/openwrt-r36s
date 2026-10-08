"""Provision disposable card images with real sfdisk and exFAT tools.

Only the kernel device/mount and UCI boundaries are simulated. All partition
writes, filesystem creation and filesystem checking use the shipped commands.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'
FILES = ROOT / 'package/system/rk3326-handheld/files'
START = 1310720
SECTORS = 1572864  # 768 MiB card, with a 128 MiB unused tail.


class StorageTests(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='test-storage-', dir=WORK)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ('sfdisk', 'mkfs.exfat', 'fsck.exfat', 'blkid'):
            self.assertIsNotNone(shutil.which(name), f'Install fdisk and exfatprogs (missing {name})')
        self.env = dict(os.environ, FIXTURE=str(self.root), REAL_MKFS=shutil.which('mkfs.exfat'))
        self.env['PATH'] = str(self.root / 'bin') + os.pathsep + self.env['PATH']
        self.disk = self.root / 'dev/mmcblk0'
        self.partition = self.root / 'dev/mmcblk0p3'
        self.write('dev/mmcblk0', '')
        with self.disk.open('r+b') as disk:
            disk.truncate(SECTORS * 512)
            mbr = bytearray(512)
            mbr[:440] = bytes(range(220)) * 2
            mbr[440:444] = b'\x12\x34\x56\x78'
            for n, kind, start, size in ((0, 12, 65536, 131072), (1, 131, 262144, 1048576)):
                struct.pack_into('<B3sB3sII', mbr, 446 + n*16, 0, b'\0'*3, kind, b'\0'*3, start, size)
            mbr[510:] = b'\x55\xaa'
            disk.write(mbr)
            for offset in (32768, 8*1024*1024, 12*1024*1024, 65536*512, 262144*512):
                disk.seek(offset)
                disk.write(b'KEEP BOOTLOADER, BOOT AND ROOT DATA')
        self.original_mbr = self.read_mbr()
        for key, value in {'partition': '2', 'start': '262144', 'size': '1048576'}.items():
            self.write('sys/devices/mmcblk0/mmcblk0p2/' + key, value)
        (self.root / 'sys/dev/block').mkdir(parents=True)
        (self.root / 'sys/dev/block/179:2').symlink_to(self.root / 'sys/devices/mmcblk0/mmcblk0p2')
        for key, value in {'size': str(SECTORS), 'ro': '0', 'queue/logical_block_size': '512'}.items():
            self.write('sys/class/block/mmcblk0/' + key, value)
        self.write('proc/self/mountinfo', '30 1 179:2 / /rom ro - squashfs /dev/root ro\n')
        self.write('proc/mounts', '')
        self.write('uci.json', '{}')
        self.write('lib/functions.sh', '''
config_load() { :; }
config_foreach() { for section in $(uci sections); do "$1" "$section"; done; }
config_get() { export "$1=$(uci get "fstab.$2.$3" || true)"; }
config_get_bool() { config_get "$@"; eval "[ -n \\\"\\$$1\\\" ] || $1=$4"; }
''')
        self.write('bin/uci', '''#!/usr/bin/env python3
import json, os, pathlib, shlex, sys
r = pathlib.Path(os.environ['FIXTURE'])
p = r / 'uci.json'
d = json.loads(p.read_text())
a = [s for s in sys.argv[1:] if s != '-q']
if a[0] == 'get':
    if a[1] not in d: sys.exit(1)
    print(d[a[1]])
elif a[0] == 'sections':
    print(' '.join(k.split('.')[1] for k,v in d.items() if k.count('.') == 1 and v == 'mount'))
elif a[0] in ('set', 'batch'):
    lines = ['set ' + shlex.quote(a[1])] if a[0] == 'set' else sys.stdin.read().splitlines()
    for line in lines:
        command, assignment = shlex.split(line)
        assert command == 'set'
        k,v = assignment.split('=',1)
        d[k] = v
    p.write_text(json.dumps(d))
elif a[0] != 'commit': sys.exit(2)
''', True)
        self.write('bin/partx', '''#!/usr/bin/env python3
import os,pathlib,struct,sys
r=pathlib.Path(os.environ['FIXTURE'])
if (r/'fail-partx').exists(): sys.exit(1)
with (r/'dev/mmcblk0').open('rb') as f:
    f.seek(478); entry=f.read(16)
start,size=struct.unpack_from('<II',entry,8)
with (r/'dev/mmcblk0p3').open('wb') as f: f.truncate(size*512)
for k,v in {'start':start,'size':size,'dev':'179:3'}.items():
    p=r/'sys/class/block/mmcblk0p3'/k
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(str(v))
''', True)
        self.write('bin/block', '''#!/usr/bin/env python3
import json,os,pathlib,subprocess,sys
r=pathlib.Path(os.environ['FIXTURE'])
if sys.argv[1]=='info':
    p=subprocess.run(['blkid','-p','-o','export',sys.argv[2]],capture_output=True,text=True)
    if p.returncode: sys.exit(p.returncode)
    d=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
    print(sys.argv[2]+': '+' '.join(k+'="'+d[k]+'"' for k in ('UUID','TYPE') if k in d))
else:
    if (r/'fail-mount').exists(): sys.exit(1)
    d=json.loads((r/'uci.json').read_text())
    for k,v in d.items():
        if k.endswith('.target') and d.get(k[:-6]+'enabled')=='1':
            (r/'proc/mounts').write_text('/dev/mmcblk0p3 '+v+' exfat rw,noatime 0 0\\n')
''', True)
        self.write('bin/mkfs.exfat', '''#!/bin/sh
echo format >> "$FIXTURE/formats"
if [ -e "$FIXTURE/fail-format" ]; then
    printf 'partial format' > "$FIXTURE/dev/mmcblk0p3"
    truncate -s 134217728 "$FIXTURE/dev/mmcblk0p3"
    exit 1
fi
exec "$REAL_MKFS" "$@"
''', True)
        self.write('bin/logger', '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FIXTURE/log"\n', True)
        # Avoid global host syncs; real journal and filesystem writes still run.
        self.write('bin/sync', '#!/bin/sh\nexit 0\n', True)
        script = (FILES / 'usr/sbin/handheld-storage').read_text()
        script = re.sub(r'/dev/|/proc/|/sys/|/etc/|/var/|/lib/|/easyroms|/roms',
                        lambda m: str(self.root) + m[0], script)
        script = script.replace('[ -b "$disk" ]', '[ -f "$disk" ]').replace('[ -b "$partition" ]', '[ -f "$partition" ]').replace('[ ! -b "$partition" ]', '[ ! -f "$partition" ]')
        script = script.replace('set -e\n', 'set -e\nsync() { :; }\n')
        self.write('storage', script, True)
        (self.root / 'etc').mkdir(exist_ok=True)

    def write(self, name, value, executable=False):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value)
        if executable: p.chmod(0o755)

    def read_mbr(self):
        with self.disk.open('rb') as f: return f.read(512)

    def run_storage(self, expected=0):
        p = subprocess.run(['busybox', 'ash', self.root / 'storage'], env=self.env,
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, expected, p.stdout + p.stderr)
        return p

    def set_partition(self, number, kind, start, size):
        with self.disk.open('r+b') as f:
            f.seek(446 + (number-1)*16)
            f.write(struct.pack('<B3sB3sII',0,b'\0'*3,kind,b'\0'*3,start,size))

    def reboot(self):
        self.write('proc/mounts','')

    def test_first_boot_uses_tail_and_preserves_os_and_repeated_boot(self):
        with self.disk.open('rb') as f: before = hashlib.file_digest(f,'sha256').hexdigest()
        self.run_storage()
        mbr=self.read_mbr()
        self.assertEqual(mbr[:478],self.original_mbr[:478])
        self.assertEqual(mbr[494:],self.original_mbr[494:])
        self.assertEqual(struct.unpack_from('<II',mbr,486),(START,SECTORS-START))
        # Restore just the new entry in a copy-free digest to compare every
        # byte outside it, including bootloader slots and both OS partitions.
        with self.disk.open('rb') as f:
            digest=hashlib.sha256(self.original_mbr)
            f.seek(512)
            while chunk:=f.read(4*1024*1024): digest.update(chunk)
        self.assertEqual(digest.hexdigest(),before)
        info=subprocess.check_output(['blkid','-p','-o','export',self.partition],text=True)
        self.assertIn('TYPE=exfat',info)
        self.assertIn('LABEL=EASYROMS',info)
        self.assertIn('ready', (self.root/'etc/easyroms.state').read_text())
        self.assertEqual((self.root/'etc/easyroms.state').stat().st_mode & 0o777,0o600)
        data=json.loads((self.root/'uci.json').read_text())
        self.assertEqual(data['fstab.easyroms.target'],str(self.root/'easyroms'))
        self.assertIn('fstab.easyroms.uuid',data)
        with self.partition.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
        self.reboot();self.run_storage();self.run_storage()
        self.assertEqual((self.root/'formats').read_text().splitlines(),['format'])
        with self.partition.open('rb') as f: self.assertEqual(hashlib.file_digest(f,'sha256').hexdigest(),digest)

    def test_interrupted_partition_registration_resumes(self):
        self.write('fail-partx','')
        self.run_storage(1)
        self.assertTrue((self.root/'etc/easyroms.state').read_text().endswith('planned\n'))
        self.assertFalse((self.root/'formats').exists())
        (self.root/'fail-partx').unlink()
        self.run_storage()

    def test_interrupted_format_resumes_before_mount(self):
        self.write('fail-format','')
        self.run_storage(1)
        self.assertTrue((self.root/'etc/easyroms.state').read_text().endswith('formatting\n'))
        self.assertEqual((self.root/'proc/mounts').read_text(),'')
        (self.root/'fail-format').unlink()
        self.run_storage()
        self.assertEqual(len((self.root/'formats').read_text().splitlines()),2)

    def test_failed_mount_does_not_format_again(self):
        self.write('fail-mount','');self.run_storage(1)
        self.assertTrue((self.root/'etc/easyroms.state').read_text().endswith('ready\n'))
        (self.root/'fail-mount').unlink();self.run_storage()
        self.assertEqual((self.root/'formats').read_text().splitlines(),['format'])

    def test_existing_unknown_third_partition_is_never_formatted(self):
        self.set_partition(3,7,START,SECTORS-START)
        before=self.read_mbr()
        self.run_storage(1)
        self.assertEqual(self.read_mbr(),before)
        self.assertFalse((self.root/'formats').exists())

    def test_existing_exfat_is_adopted_without_formatting(self):
        self.run_storage()
        with self.partition.open('rb') as f: before=hashlib.file_digest(f,'sha256').hexdigest()
        self.reboot();self.write('uci.json','{}');(self.root/'etc/easyroms.state').unlink()
        self.run_storage()
        self.assertEqual((self.root/'formats').read_text().splitlines(),['format'])
        with self.partition.open('rb') as f: self.assertEqual(hashlib.file_digest(f,'sha256').hexdigest(),before)

    def test_wrong_layout_or_fourth_partition_is_untouched(self):
        for number,kind,start,size in ((2,131,262144,2097152),(3,131,START,100000),(4,7,START,100000)):
            with self.subTest(number=number):
                with self.disk.open('r+b') as f: f.write(self.original_mbr)
                self.set_partition(number,kind,start,size)
                before=self.read_mbr()
                self.run_storage(1)
                self.assertEqual(self.read_mbr(),before)
                self.assertFalse((self.root/'formats').exists())

    def test_insufficient_space_and_readonly_cards_are_untouched(self):
        for key,value in (('size',str(START+1000)),('ro','1'),('queue/logical_block_size','4096')):
            with self.subTest(key=key):
                self.write('sys/class/block/mmcblk0/'+key,value)
                self.run_storage(1)
                self.assertEqual(self.read_mbr(),self.original_mbr)
                self.assertFalse((self.root/'formats').exists())
                self.write('sys/class/block/mmcblk0/'+key,{'size':str(SECTORS),'ro':'0','queue/logical_block_size':'512'}[key])

    def test_mismatched_journal_and_mounted_partition_are_not_formatted(self):
        self.write('etc/easyroms.state','v1 wrong 1572864 1310720 262144 formatting\n')
        self.run_storage(1)
        self.assertEqual(self.read_mbr(),self.original_mbr)
        (self.root/'etc/easyroms.state').unlink()
        self.write('proc/self/mountinfo',(self.root/'proc/self/mountinfo').read_text()+'31 1 179:3 / /elsewhere rw - exfat /dev/card rw\n')
        self.run_storage(1)
        self.assertFalse((self.root/'formats').exists())

    def test_custom_games_card_prevents_automatic_partitioning(self):
        self.write('uci.json',json.dumps({'fstab.games':'mount','fstab.games.target':str(self.root/'roms'),'fstab.games.enabled':'1'}))
        self.run_storage()
        self.assertEqual(json.loads((self.root/'uci.json').read_text())['fstab.games.target'],str(self.root/'easyroms'))
        self.assertEqual(self.read_mbr(),self.original_mbr)
        self.assertFalse((self.root/'formats').exists())
        self.reboot();self.write('fail-mount','');self.run_storage(1)
        self.assertEqual(self.read_mbr(),self.original_mbr)


if __name__ == '__main__': unittest.main()
