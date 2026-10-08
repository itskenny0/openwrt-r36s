#!/usr/bin/env python3
"""Run the packaged upgrade validator and gzip failure path with target tools."""
import gzip
import os
from pathlib import Path
import shutil
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[1]
rootfs = ROOT / 'build_dir/target-aarch64_cortex-a35_musl/root-rk3326'
work = ROOT / '.work/upgrade-smoke'
work.mkdir(parents=True, exist_ok=True)
(work / 'proot-tmp').mkdir(exist_ok=True)
(work / 'tmp').mkdir(exist_ok=True)
source = ROOT / 'bin/targets/rk3326/generic/openwrt-rk3326-generic-gameconsole_r36s-squashfs-sysupgrade.img.gz'
image = work / 'image.img.gz'
image.unlink(missing_ok=True)
os.link(source, image)
with source.open('rb') as f:
    header = zlib.decompressobj(31).decompress(f.read(65536), 512)
assert header[510:512] == b'\x55\xaa'
(work / 'disk').write_bytes(header)
(work / 'meta.json').write_text('{"metadata_version":"1.1","supported_devices":["test"]}')
# Preserve the real fwtool container checksum around an invalid gzip checksum.
corrupt = bytearray(gzip.compress(b'CRC fixture'))
corrupt[-8] ^= 1
(work / 'corrupt.img.gz').write_bytes(corrupt)
subprocess.run([str(ROOT / 'staging_dir/host/bin/fwtool'), '-I', str(work / 'meta.json'),
                str(work / 'corrupt.img.gz')], check=True)
platform = (rootfs / 'lib/upgrade/platform.sh').read_text().replace('"/dev/$diskdev"', '"/test/$diskdev"')
(work / 'platform.sh').write_text(platform)
script = '''set -x
set -o pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
. /lib/upgrade/common.sh
. /test/platform.sh
export_bootdevice() { return 0; }
export_partdevice() { export "$1=disk"; }
platform_check_image /test/image.img.gz || exit 1
if rk3326_image_stream /test/corrupt.img.gz > /dev/null; then
    echo 'Corrupt gzip was accepted' >&2
    exit 1
fi
'''
env = dict(os.environ, PROOT_TMP_DIR=str(work / 'proot-tmp'), TMPDIR=str(work))
with (work / 'validation.log').open('w') as log:
    result = subprocess.run(['proot', '-r', str(rootfs), '-b', str(work) + ':/test', '-b', str(work / 'tmp') + ':/tmp', '-b', '/dev',
                             '-w', '/', '-q', shutil.which('qemu-aarch64'), '/bin/sh', '-c', script],
                            env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
if result.returncode:
    raise RuntimeError(f'Packaged upgrade validator failed: {work / "validation.log"}')
print('Packaged upgrade validator accepted the R36S image and rejected a corrupt gzip with valid fwtool metadata.')
