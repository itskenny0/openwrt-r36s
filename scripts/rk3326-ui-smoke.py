#!/usr/bin/env python3
"""Render the target frontend and exercise menus/game launches under QEMU.

proot confines target shell commands to a disposable filesystem. Only the USB
helper boundary and graphics/input/audio devices are simulated; ES, RetroArch,
Gambatte, the launcher and their target libraries are the shipped binaries.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--scenario", choices=("all", "usb", "settings", "game"), default="all")
scenario = parser.parse_args().scenario
stage = ROOT / "staging_dir/target-aarch64_cortex-a35_musl"
source = ROOT / "build_dir/target-aarch64_cortex-a35_musl/root-rk3326"
work = ROOT / ".work/ui-smoke"
root = work / "root"
work.mkdir(parents=True, exist_ok=True)
if root.exists():
    shutil.rmtree(root)
shutil.copytree(source, root, symlinks=True)
for path in ("test", "root/.emulationstation", "roms/gb"):
    (root / path).mkdir(parents=True, exist_ok=True)
(work / "proot-tmp").mkdir(exist_ok=True)
env = dict(os.environ, STAGING_DIR=str(stage), PROOT_TMP_DIR=str(work / "proot-tmp"), TMPDIR=str(work))


def write(path, content, executable=False):
    file = root / path
    file.write_text(content)
    if executable:
        file.chmod(0o755)


compiler, = ROOT.glob("staging_dir/toolchain-*/bin/aarch64-openwrt-linux-musl-gcc")
subprocess.run([str(compiler), "-shared", "-fPIC", "-I" + str(stage / "usr/include"),
                str(ROOT / "tests/runtime/ui.c"), "-L" + str(stage / "usr/lib"),
                "-Wl,-rpath-link," + str(stage / "usr/lib"), "-lSDL2", "-lGLESv2", "-lpng", "-ldl",
                "-o", str(root / "test/ui.so")], env=env, check=True)
keys = {"a": 97, "b": 98, "start": 13, "select": 32, "up": 1073741906,
        "down": 1073741905, "left": 1073741904, "right": 1073741903}
write("root/.emulationstation/es_input.cfg",
      '<inputList><inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">' +
      "".join(f'<input name="{key}" type="key" id="{value}" value="1" />' for key, value in keys.items()) +
      '</inputConfig></inputList>')
# The shell/kernel USB boundary has its own tests in tests/test_handheld.py.
write("usr/sbin/handheld-usb", '''#!/bin/sh
printf '%s\\n' "$1" >> /test/usb-calls
case "$1" in
status) [ -e /test/usb-enabled ] ;;
gadget) touch /test/usb-enabled ;;
host) rm -f /test/usb-enabled ;;
address) echo 192.168.1.1 ;;
esac
''', executable=True)

write("usr/sbin/handheld-settings", '''#!/bin/sh
printf '%s %s\\n' "$1" "${2:-}" >> /test/settings-calls
case "$1" in
brightness-get) cat /test/brightness ;;
brightness-set) echo "$2" > /test/brightness ;;
volume-get) cat /test/volume ;;
volume-set) echo "$2" > /test/volume ;;
*) exit 1 ;;
esac
''', executable=True)
write("test/brightness", "50\n")
write("test/volume", "70\n")


def frontend(name, actions, startup="tools"):
    write("root/.emulationstation/es_settings.cfg",
          '<string name="ThemeSet" value="openwrt" />\n'
          '<bool name="EnableSounds" value="false" />\n'
          '<string name="TransitionStyle" value="instant" />\n'
          f'<string name="StartupSystem" value="{startup}" />\n')
    write("test/actions", actions)
    for image in (root / "test").glob("frame-*.png"):
        image.unlink()
    command = ["proot", "-r", str(root), "-b", "/dev", "-b", "/proc", "-w", "/",
               "-q", shutil.which("qemu-aarch64"), "/bin/sh", "-c",
               "export PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/root SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy "
               "EGL_PLATFORM=surfaceless GALLIUM_DRIVER=softpipe LD_PRELOAD=/test/ui.so; "
               "exec /usr/bin/emulationstation --windowed --resolution 640 480 --no-splash --debug"]
    with (work / f"{name}.log").open("w") as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            result = process.wait(timeout=600)
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    if result:
        raise RuntimeError(f"Frontend {name} exited {result}; see {work / (name + '.log')}")
    for line in actions.splitlines():
        number, action = line.split()
        if action == "capture":
            image = root / "test" / f"frame-{int(number):03d}.png"
            if not image.exists() or image.stat().st_size < 1000:
                raise RuntimeError(f"Missing rendered frame: {image}")
            shutil.copy2(image, work / f"{name}-{image.name}")


menu = """3 Return
6 capture
7 Down
8 A
11 capture
12 A
13 B
16 capture
17 B
18 quit
"""
if scenario in ("all", "usb"):
    frontend("usb-enable", menu)
    assert (root / "test/usb-enabled").exists(), "Native USB setting did not enable the helper"
    frontend("usb-disable", menu)
    assert not (root / "test/usb-enabled").exists(), "Native USB setting did not restore its saved state"
    assert (root / "test/usb-calls").read_text().splitlines() == ["status", "gadget", "status", "host"]
if scenario == "usb":
    print("Rendered ES menus and persistent USB toggle passed.")
    raise SystemExit(0)

if scenario in ("all", "settings"):
    frontend("brightness", """3 Return
6 Down
7 Down
8 Down
9 A
12 capture
13 Right
14 B
17 capture
18 B
19 quit
""")
    assert (root / "test/brightness").read_text().strip() == "55", "Brightness was not saved from the native menu"
    frontend("volume", """3 Return
6 Down
7 Down
8 A
11 capture
12 Left
13 B
16 B
17 quit
""")
    assert (root / "test/volume").read_text().strip() == "69", "Volume was not saved from the native menu"
    assert (root / "test/settings-calls").read_text().splitlines() == [
        "brightness-get ", "brightness-set 55", "volume-get ", "volume-set 69"]
if scenario == "settings":
    print("Rendered brightness and volume controls passed.")
    raise SystemExit(0)

# Run a real core through the real launcher; bound execution for unattended CI.
spec = importlib.util.spec_from_file_location("roms", ROOT / "tests/runtime/roms.py")
roms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roms)
(root / "roms/gb/runtime.gb").write_bytes(roms.game_boy())
config = (root / "etc/retroarch.cfg").read_text()
for setting in ("video_driver", "audio_driver", "input_driver", "input_joypad_driver"):
    config = re.sub(rf'^{setting}\s*=.*$', f'{setting} = "null"', config, flags=re.MULTILINE)
write("etc/retroarch.cfg", config)
(root / "usr/bin/retroarch").rename(root / "usr/bin/retroarch.real")
write("usr/bin/retroarch", '''#!/bin/sh
unset LD_PRELOAD
exec /usr/bin/retroarch.real --verbose --max-frames=60 "$@"
''', executable=True)
frontend("game", """3 A
6 capture
7 A
11 capture
12 remove-game
13 A
16 capture
17 A
18 quit
""", "gb")
save = (root / "roms/saves/gb/runtime.srm").read_bytes()
assert len(save) == 8192 and save[0] == 0x5b, "The frontend did not save and reload cartridge RAM across two launches"
log = (work / "game.log").read_text()
assert "launch terminated with nonzero exit code" in log, "Missing game was not reported"
gamelist = ET.parse(root / "root/.emulationstation/gamelists/gb/gamelist.xml")
assert gamelist.findtext("game/playcount") == "2", "Failed launch was counted as a played game"
print("Rendered ES game launch/save/reload/return and failed-launch dialog passed.")
