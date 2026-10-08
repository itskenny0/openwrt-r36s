#!/usr/bin/env python3
"""Run first-boot storage with packaged ARM64 tools on a disposable SD image.

Only block-device registration, probing and mounting are simulated. The target
shell, OpenWrt UCI/functions, storage helper, sfdisk and exFAT tools are real.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'build_dir/target-aarch64_cortex-a35_musl/root-rk3326'
work = ROOT / '.work/storage-smoke'
root = work / 'root'
work.mkdir(parents=True, exist_ok=True)
if root.exists(): shutil.rmtree(root)
shutil.copytree(source, root, symlinks=True)
for path in ('test', 'dev', 'proc/self', 'sys/dev/block', 'etc/config', 'tmp/.uci', 'tmp/lock'):
    (root / path).mkdir(parents=True, exist_ok=True)
(work / 'proot-tmp').mkdir(exist_ok=True)
env = dict(os.environ, PROOT_TMP_DIR=str(work / 'proot-tmp'), TMPDIR=str(work))


def write(path, text, executable=False):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    if executable: p.chmod(0o755)


spec = importlib.util.spec_from_file_location('images', ROOT / 'scripts/rk3326-check-images.py')
images = importlib.util.module_from_spec(spec)
spec.loader.exec_module(images)
disk = root / 'dev/mmcblk0'
images.unpack_image(ROOT / 'bin/targets/rk3326/generic/openwrt-rk3326-generic-gameconsole_r36s-squashfs-sdcard.img.gz', disk, allow_trailer=False)
with disk.open('r+b') as f:
    mbr = f.read(512)
    f.truncate(768 * 1024 * 1024)
with disk.open('rb') as f: before = hashlib.file_digest(f, 'sha256').hexdigest()
for name, value in {'partition': '2', 'start': '262144', 'size': '1048576'}.items():
    write('sys/devices/mmcblk0/mmcblk0p2/' + name, value)
(root / 'sys/dev/block/179:2').symlink_to('../../devices/mmcblk0/mmcblk0p2')
for name, value in {'size': '1572864', 'ro': '0', 'queue/logical_block_size': '512'}.items():
    write('sys/class/block/mmcblk0/' + name, value)
write('proc/self/mountinfo', '30 1 179:2 / /rom ro - squashfs /dev/root ro\n')
write('proc/mounts', '')
with (root / 'test/empty-volume').open('wb') as f: f.truncate(128 * 1024 * 1024)
write('etc/config/fstab', "config global\n\toption anon_mount '0'\n")
helper = (root / 'usr/sbin/handheld-storage').read_text()
helper = helper.replace('set -e\n', 'set -e\nsync() { :; }\n')
helper = helper.replace('[ -b "$disk" ]', '[ -f "$disk" ]').replace('[ -b "$partition" ]', '[ -f "$partition" ]').replace('[ ! -b "$partition" ]', '[ ! -f "$partition" ]')
write('test/storage', helper, True)
write('test/partx', '''#!/bin/sh
set -e
# Assert that the packaged partx also understands the new on-disk partition.
set -- $(/usr/sbin/partx --nr 3 --raw --noheadings --output START,SECTORS /dev/mmcblk0)
[ "$1 $2" = '1310720 262144' ]
mv /test/empty-volume /dev/mmcblk0p3
mkdir -p /sys/class/block/mmcblk0p3
echo "$1" > /sys/class/block/mmcblk0p3/start
echo "$2" > /sys/class/block/mmcblk0p3/size
echo 179:3 > /sys/class/block/mmcblk0p3/dev
''', True)
write('test/block', '''#!/bin/sh
set -e
case "$1" in
info)
    [ "$(dd if="$2" bs=1 skip=3 count=8 2>/dev/null)" = 'EXFAT   ' ] || exit 0
    serial=$(hexdump -v -s 100 -n 4 -e '1/4 "%08X"' "$2")
    uuid="${serial%????}-${serial#????}"
    echo "$2: UUID=\\"$uuid\\" TYPE=\\"exfat\\""
    ;;
mount)
    target=$(uci -q get fstab.easyroms.target)
    [ "$(uci -q get fstab.easyroms.enabled)" = 1 ]
    [ -n "$(uci -q get fstab.easyroms.uuid)" ]
    echo "/dev/mmcblk0p3 $target exfat rw,noatime 0 0" > /proc/mounts
    ;;
*) exit 1 ;;
esac
''', True)
write('test/logger', '#!/bin/sh\necho "$*"\n', True)
command = ['proot', '-r', str(root), '-b', '/dev/null', '-w', '/', '-q', shutil.which('qemu-aarch64'),
           '/bin/sh', '-c']


def run(name, shell):
    with (work / (name + '.log')).open('w') as log:
        subprocess.run(command + ['export PATH=/test:/usr/sbin:/usr/bin:/sbin:/bin; ' + shell],
                       env=env, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=120)


run('first-boot', '/bin/sh /test/storage')
assert (root / 'etc/easyroms.state').read_text().endswith('ready\n')
assert '/easyroms exfat rw' in (root / 'proc/mounts').read_text()
with disk.open('rb') as f:
    current = f.read(512)
    assert current[:478] == mbr[:478] and current[494:] == mbr[494:]
    assert struct.unpack_from('<II', current, 486) == (1310720, 262144)
    digest = hashlib.sha256(mbr)
    while chunk := f.read(4 * 1024 * 1024): digest.update(chunk)
assert digest.hexdigest() == before, 'The first boot changed existing OS data'
partition = root / 'dev/mmcblk0p3'
with partition.open('rb') as f: formatted = hashlib.file_digest(f, 'sha256').hexdigest()
run('check-exfat', '/usr/sbin/fsck.exfat -n /dev/mmcblk0p3')
write('proc/mounts', '')
run('second-boot', '/bin/sh /test/storage')
# A reset sysupgrade removes configuration but preserves partition 3.
write('etc/config/fstab', "config global\n\toption anon_mount '0'\n")
(root / 'etc/easyroms.state').unlink()
write('proc/mounts', '')
run('reset-upgrade', '/bin/sh /test/storage')
with partition.open('rb') as f:
    assert hashlib.file_digest(f, 'sha256').hexdigest() == formatted, 'An existing volume was changed'
# Check the actual target sed/UCI-defaults migration of retained settings.
write('etc/retroarch.cfg', 'system_directory = "/roms/bios"\nsavefile_directory = "/roms/saves"\nsavestate_directory = "/custom/states"\n')
write('etc/emulationstation/es_systems.cfg', '<systemList><system><path>/roms/gb</path></system></systemList>\n')
run('migrate-paths', '/bin/sh /etc/uci-defaults/31-easyroms-paths')
assert '"/easyroms/bios"' in (root / 'etc/retroarch.cfg').read_text()
assert '"/custom/states"' in (root / 'etc/retroarch.cfg').read_text()
assert '<path>/easyroms/gb</path>' in (root / 'etc/emulationstation/es_systems.cfg').read_text()
print('Packaged ARM64 storage provisioned exFAT, preserved OS data, mounted /easyroms and retained it across normal/reset boots.')
