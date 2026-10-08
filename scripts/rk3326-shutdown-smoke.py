#!/usr/bin/env python3
"""Check that service shutdown flushes and reloads a real emulator's saves.

Only the waiting frontend and hardware devices are simulated. The supervisor,
launcher, target shell, RetroArch and Gambatte come from the packaged image.
"""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'build_dir/target-aarch64_cortex-a35_musl/root-rk3326'
work = ROOT / '.work/shutdown-smoke'
root = work / 'root'
work.mkdir(parents=True, exist_ok=True)
if root.exists():
    shutil.rmtree(root)
shutil.copytree(source, root, symlinks=True)
for path in ('test', 'roms/gb'):
    (root / path).mkdir(parents=True, exist_ok=True)
(work / 'proot-tmp').mkdir(exist_ok=True)
env = dict(os.environ, PROOT_TMP_DIR=str(work / 'proot-tmp'), TMPDIR=str(work))


def write(path, text, executable=False):
    path = root / path
    path.write_text(text)
    if executable:
        path.chmod(0o755)


spec = importlib.util.spec_from_file_location('roms', ROOT / 'tests/runtime/roms.py')
roms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roms)
(root / 'roms/gb/runtime.gb').write_bytes(roms.game_boy())
config = (root / 'etc/retroarch.cfg').read_text()
for setting in ('video_driver', 'audio_driver', 'input_driver', 'input_joypad_driver'):
    config = re.sub(rf'^{setting}\s*=.*$', f'{setting} = "null"', config, flags=re.MULTILINE)
config += '\nautosave_interval = "0"\n'
write('etc/retroarch.cfg', config)
(root / 'usr/bin/retroarch').rename(root / 'usr/bin/retroarch.real')
write('usr/bin/retroarch', '''#!/bin/sh
echo "$$" > /test/emulator-pid
exec /usr/bin/retroarch.real --verbose "$@"
''', executable=True)
# SDL queues a quit event while ES waits for its game child to return.
write('usr/bin/emulationstation', '''#!/bin/sh
trap ':' TERM
echo "$$" > /test/session-pid
/usr/bin/handheld-retroarch gb /roms/gb/runtime.gb &
game=$!
wait "$game" || wait "$game"
''', executable=True)
supervisor = (source / 'usr/bin/emulationstation-session').read_text()
supervisor = 'child=\n' + supervisor.split('child=\n', 1)[1]
supervisor = supervisor.replace(' < /dev/tty1 > /dev/tty1 2>&1', '').replace('setsid -c', 'setsid')
write('test/supervisor', '#!/bin/sh\nrotation=0\necho "$$" > /test/supervisor-pid\n' + supervisor)
command = ['proot', '-r', str(root), '-b', '/dev', '-b', '/proc', '-w', '/',
           '-q', shutil.which('qemu-aarch64'), '/bin/sh', '-c',
           'export PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/root; exec /bin/sh /test/supervisor']
for attempt, marker in enumerate((0x5a, 0x5b), 1):
    for file in (root / 'test').glob('*-pid'):
        file.unlink()
    logpath = root / 'tmp/handheld/retroarch.log'
    logpath.unlink(missing_ok=True)
    with (work / f'shutdown-{attempt}.log').open('w') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 120
            while not logpath.exists() or '[Playlist] Loading history' not in logpath.read_text():
                if process.poll() is not None:
                    raise RuntimeError('Emulator exited before startup; inspect shutdown logs')
                if time.monotonic() > deadline:
                    raise TimeoutError('Emulator did not finish startup')
                time.sleep(0.1)
            # The original cartridge writes its RAM marker in its first frame.
            time.sleep(2)
            os.kill(int((root / 'test/supervisor-pid').read_text()), signal.SIGTERM)
            assert process.wait(timeout=30) == 0, 'Supervisor failed to stop'
            save = (root / 'roms/saves/gb/runtime.srm').read_bytes()
            assert len(save) == 8192 and save[0] == marker, 'Shutdown did not flush/reload cartridge RAM'
            assert '[SRAM] Saved successfully' in logpath.read_text(), 'Missing save completion'
        finally:
            for file in (root / 'test').glob('*-pid'):
                try: os.kill(int(file.read_text()), signal.SIGKILL)
                except ProcessLookupError: pass
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            if logpath.exists():
                shutil.copy2(logpath, work / f'emulator-{attempt}.log')
print('Packaged RetroArch flushed saves on service shutdown and restored them on the next launch.')
