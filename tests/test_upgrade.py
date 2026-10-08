"""Run the upgrade hooks against file-backed disks and injected I/O failures.

No command in this suite opens a real block device. The MBR and compressed
payload are real; only OpenWrt boot-device discovery and fwtool extraction are
substituted. The runtime smoke test checks the actual target fwtool boundary.
"""
import gzip
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'
MIB = 1024 * 1024


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix='upgrade-image-', dir=WORK)
        cls.image = Path(cls.shared.name) / 'image.gz'
        cls.mbr = bytearray(512)
        cls.mbr[440:444] = b'DISK'
        cls.mbr[510:] = b'\x55\xaa'
        for offset, kind, start, size in ((446, 0x0c, 65536, 131072), (462, 0x83, 262144, 2)):
            cls.mbr[offset + 4] = kind
            struct.pack_into('<II', cls.mbr, offset + 8, start, size)
        with gzip.open(cls.image, 'wb', compresslevel=1) as stream:
            stream.write(cls.mbr)
            stream.write(bytes(MIB - 512))
            for _ in range(127): stream.write(bytes(MIB))
            stream.write(b'R' * 1024)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='test-upgrade-', dir=WORK)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for path in ('bin', 'dev', 'tmp', 'mnt/overlays'):
            (self.root / path).mkdir(parents=True)
        self.env = dict(os.environ, FIXTURE=str(self.root), UPGRADE_BACKUP=str(self.root / 'backup.tgz'),
                        BACKUP_FILE='sysupgrade.tgz')
        self.env['PATH'] = str(self.root / 'bin') + os.pathsep + self.env['PATH']
        self.write('dev/disk', self.mbr)
        self.write('dev/disk1', b'old boot')
        self.write('dev/disk2', b'old root')
        self.write('backup.tgz', b'configuration')
        self.write('mnt/boot.env', b'overlay=panel.dtbo')
        self.write('mnt/overlays/panel.dtbo', b'panel')
        self.write('bin/fwtool', '#!/bin/sh\nfor arg; do :; done\ncat "$arg"\n')
        for tool in ('mount', 'umount', 'sync'):
            self.write('bin/' + tool, '#!/bin/sh\nexit 0\n')
        source = ROOT / 'target/linux/rk3326/base-files/lib/upgrade/platform.sh'
        script = source.read_text()
        common = (ROOT / 'package/base-files/files/lib/upgrade/common.sh').read_text()
        # Execute the real partition parser, with test files instead of /dev.
        for prefix in ('/tmp/', '/mnt', '/dev/$'):
            script = script.replace(prefix, str(self.root) + prefix)
            common = common.replace(prefix, str(self.root) + prefix)
        self.write('common.sh', common)
        self.write('platform.sh', script)
        self.write('run', '''#!/bin/bash
. "$FIXTURE/common.sh"
. "$FIXTURE/platform.sh"
export_bootdevice() { return 0; }
export_partdevice() {
    [ "${MISSING_PART:-}" != "$2" ] || return 1
    if [ "$2" = 0 ]; then export "$1=disk"; else export "$1=disk$2"; fi
}
"$@"
printf complete > "$FIXTURE/completed"
''')

    def write(self, name, data):
        path = self.root / name
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        path.chmod(0o755)

    def run_hook(self, hook, expected=0, image=None):
        (self.root / 'completed').unlink(missing_ok=True)
        result = subprocess.run([self.root / 'run', hook, image or self.image], env=self.env,
                                capture_output=True, text=True)
        if expected == 0:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((self.root / 'completed').exists(), 'Dispatcher continued after a failed hook')

    def test_preserve_panel_configuration_and_disk_signature(self):
        # An extra games partition remains untouched.
        disk = bytearray(self.mbr)
        disk[478 + 4] = 0x07
        struct.pack_into('<II', disk, 478 + 8, 270000, 1000)
        self.write('dev/disk', disk)
        self.write('dev/disk3', b'games and saves')
        self.run_hook('platform_pre_upgrade')
        self.write('mnt/boot.env', b'image defaults')
        self.run_hook('platform_do_upgrade')
        self.run_hook('platform_copy_config')
        self.assertEqual((self.root / 'dev/disk2').read_bytes(), b'R' * 1024)
        self.assertEqual((self.root / 'dev/disk').read_bytes(), disk)
        self.assertEqual((self.root / 'dev/disk3').read_bytes(), b'games and saves')
        self.assertEqual((self.root / 'mnt/boot.env').read_text(), 'overlay=panel.dtbo')
        self.assertEqual((self.root / 'mnt/sysupgrade.tgz').read_bytes(), b'configuration')

    def test_corrupt_and_short_streams_stop_before_writing(self):
        corrupt = self.root / 'corrupt.gz'
        data = bytearray(self.image.read_bytes())
        data[-8] ^= 1
        corrupt.write_bytes(data)
        self.run_hook('platform_do_upgrade', expected=1, image=corrupt)
        corrupt.write_bytes(self.image.read_bytes()[:-20])
        self.run_hook('platform_do_upgrade', expected=1, image=corrupt)
        with gzip.open(corrupt, 'wb') as stream: stream.write(self.mbr)
        self.run_hook('platform_do_upgrade', expected=1, image=corrupt)
        self.assertEqual((self.root / 'dev/disk1').read_bytes(), b'old boot')

    def test_changed_layout_and_missing_partition_stop_before_writing(self):
        disk = bytearray(self.mbr)
        struct.pack_into('<I', disk, 462 + 12, 3)
        self.write('dev/disk', disk)
        self.run_hook('platform_do_upgrade', expected=1)
        self.write('dev/disk', self.mbr)
        self.env['MISSING_PART'] = '2'
        self.run_hook('platform_do_upgrade', expected=1)
        self.assertEqual((self.root / 'dev/disk1').read_bytes(), b'old boot')

    def test_invalid_mbr_and_repartition_request_are_rejected(self):
        self.write('dev/disk', bytes(512))
        self.run_hook('platform_do_upgrade', expected=1)
        self.write('dev/disk', self.mbr)
        self.env['UPGRADE_OPT_SAVE_PARTITIONS'] = '0'
        self.run_hook('platform_do_upgrade', expected=1)
        self.assertEqual((self.root / 'dev/disk1').read_bytes(), b'old boot')

    def test_write_failure_stops_dispatcher_and_remaining_writes(self):
        self.write('bin/dd', '''#!/bin/sh
for arg; do
    [ "$arg" != "of=$FIXTURE/dev/disk1" ] || exit 1
done
exec /usr/bin/dd "$@"
''')
        self.run_hook('platform_do_upgrade', expected=1)
        self.assertEqual((self.root / 'dev/disk2').read_bytes(), b'old root')

    def test_backup_and_restore_failures_stop_dispatcher(self):
        self.write('bin/cp', '#!/bin/sh\nexit 1\n')
        self.run_hook('platform_pre_upgrade', expected=1)
        self.run_hook('platform_copy_config', expected=1)
        self.assertEqual((self.root / 'dev/disk1').read_bytes(), b'old boot')
