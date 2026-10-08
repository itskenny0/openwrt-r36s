"""Check input safety, persistent settings and mainline boundary failures."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'


class ControlTests(unittest.TestCase):
    def test_input_state_machine(self):
        with tempfile.TemporaryDirectory(prefix='test-controls-', dir=WORK) as temp:
            binary = Path(temp) / 'controls'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-function', '-Wno-unused-variable',
                            '-fsanitize=undefined', str(ROOT / 'tests/runtime/controls.c'),
                            '-o', str(binary)], check=True)
            subprocess.run([binary], check=True)

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='test-settings-', dir=WORK)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for path in ('bin', 'var/lock', 'sys/class/backlight/panel'):
            (self.root / path).mkdir(parents=True)
        self.env = dict(os.environ, FIXTURE=str(self.root))
        self.env['PATH'] = str(self.root / 'bin') + os.pathsep + self.env['PATH']
        self.write('sys/class/backlight/panel/brightness', '128')
        self.write('sys/class/backlight/panel/max_brightness', '255')
        self.write('volume', '70')
        self.write('uci.json', json.dumps({'handheld.audio.volume': '70', 'handheld.display.brightness': '50'}))
        self.write('bin/uci', '''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE'])
path = root / 'uci.json'
data = json.loads(path.read_text())
args = [x for x in sys.argv[1:] if x != '-q']
if args[0] == 'get':
    if args[1] not in data: sys.exit(1)
    print(data[args[1]])
elif args[0] == 'set':
    key, value = args[1].split('=', 1)
    data[key] = value
    path.write_text(json.dumps(data))
elif args[0] == 'commit':
    if os.environ.get('FAIL_COMMIT'): sys.exit(1)
    with (root / 'commits').open('a') as f: f.write('commit\\n')
''')
        self.write('bin/amixer', '''#!/usr/bin/env python3
import os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE'])
args = [x for x in sys.argv[1:] if x != '-q']
if os.environ.get('FAIL_MIXER'): sys.exit(1)
if args[0] == 'sget': print('Mono: [' + (root / 'volume').read_text() + '%]')
elif args[1] == 'Master': (root / 'volume').write_text(args[2].rstrip('%'))
elif args[1] == 'Playback Mux': (root / 'route').write_text(args[2])
''')
        source = ROOT / 'package/system/rk3326-handheld/files/usr/sbin/handheld-settings'
        script = source.read_text().replace('/sys/', str(self.root) + '/sys/').replace('/var/', str(self.root) + '/var/')
        self.write('settings', script)

    def write(self, name, value):
        path = self.root / name
        path.write_text(value)
        path.chmod(0o755)

    def run_settings(self, *args, expected=0):
        result = subprocess.run(['busybox', 'ash', str(self.root / 'settings'), *args], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout.strip()

    def test_volume_steps_defer_flash_writes_and_restore(self):
        self.run_settings('volume-step', 'up')
        self.assertEqual(self.run_settings('volume-get'), '75')
        self.assertFalse((self.root / 'commits').exists())
        self.run_settings('volume-save')
        self.run_settings('volume-save')
        self.assertEqual((self.root / 'commits').read_text().splitlines(), ['commit'])
        self.run_settings('volume-step', 'down')
        self.run_settings('restore')
        self.assertEqual(self.run_settings('volume-get'), '75')
        self.run_settings('volume-set', '0')
        self.run_settings('volume-step', 'down')
        self.assertEqual(self.run_settings('volume-get'), '0')
        self.run_settings('volume-set', '100')
        self.run_settings('volume-step', 'up')
        self.assertEqual(self.run_settings('volume-get'), '100')

    def test_brightness_persistence_limits_and_headphones(self):
        self.run_settings('brightness-set', '005')
        self.assertEqual((self.root / 'sys/class/backlight/panel/brightness').read_text().strip(), '13')
        self.run_settings('brightness-set', '100')
        self.assertEqual(self.run_settings('brightness-get'), '100')
        self.write('sys/class/backlight/panel/brightness', '1')
        self.run_settings('restore')
        self.assertEqual(self.run_settings('brightness-get'), '100')
        for value in ('0', '101', '-1', '1;exit', '99999', ''):
            self.run_settings('brightness-set', value, expected=1)
        self.run_settings('route', 'headphones')
        self.assertEqual((self.root / 'route').read_text(), 'HP')
        self.run_settings('route', 'speaker')
        self.assertEqual((self.root / 'route').read_text(), 'SPK')

    def test_missing_mixer_and_failed_persistence_report_errors(self):
        self.env['FAIL_MIXER'] = '1'
        self.run_settings('volume-set', '30', expected=1)
        self.run_settings('volume-save', expected=1)
        self.assertFalse((self.root / 'commits').exists())
        del self.env['FAIL_MIXER']
        self.env['FAIL_COMMIT'] = '1'
        self.run_settings('brightness-set', '40', expected=1)
        self.run_settings('volume-set', '30', expected=1)
