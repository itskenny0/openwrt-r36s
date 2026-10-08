"""Exercise game launches, save isolation and error reporting without hardware."""
import json
import os
import signal
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work"
WORK.mkdir(exist_ok=True)
FILES = ROOT / "package/games/retroarch/files"


class LaunchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="test-game-", dir=WORK)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.env = dict(os.environ, FIXTURE=str(self.root))
        for directory in ("usr/bin", "usr/lib/libretro", "usr/share/retroarch/system/PPSSPP",
                          "etc/config", "lib", "proc", "roms", "tmp/handheld", "var/lock"):
            (self.root / directory).mkdir(parents=True)
        self.write("usr/share/retroarch/systems.tsv", (FILES / "systems.tsv").read_text())
        for name in ("gambatte", "snes9x", "genesis_plus_gx", "mednafen_pce_fast", "ppsspp"):
            self.write(f"usr/lib/libretro/{name}_libretro.so", "fixture")
        self.write("usr/share/retroarch/system/PPSSPP/compat.ini", "fixture")
        self.write("usr/bin/handheld-rotation", "#!/bin/sh\necho 1\n", executable=True)
        self.write("usr/bin/retroarch", '''#!/usr/bin/env python3
import json, os, pathlib, signal, sys, time
root = pathlib.Path(os.environ["FIXTURE"])
(root / "arguments.json").write_text(json.dumps(sys.argv[1:]))
(root / "emulator-pid").write_text(str(os.getpid()))
stopping = 0
def stop(signum, frame):
    global stopping
    stopping += 1
    if stopping > 1:
        os._exit(1)
signal.signal(signal.SIGTERM, stop)
if os.environ.get("WAIT_FOR_STOP"):
    (root / "ready").touch()
    while not stopping: time.sleep(0.01)
    # Match RetroArch's deferred cleanup: a second signal forces exit before
    # its normal main loop has finished writing cartridge RAM/save states.
    time.sleep(0.2)
    (root / "flushed").write_text("saved")
sys.exit(int(os.environ.get("CORE_EXIT", 0)))
''', executable=True)
        for name in ("handheld-retroarch", "handheld-game-dirs"):
            script = (FILES / name).read_text()
            for prefix in ("/usr/", "/etc/", "/roms", "/tmp/handheld", "/var/lock", "/lib/functions.sh", "/proc/mounts"):
                script = script.replace(prefix, str(self.root) + prefix)
            self.write("usr/bin/" + name, script, executable=True)
        self.env["PATH"] = str(self.root / "usr/bin") + os.pathsep + self.env["PATH"]
        self.rom = self.root / "roms/a game 'with quotes' $(touch INJECTED).gb"
        self.rom.write_text("test content")

    def write(self, name, text, executable=False):
        path = self.root / name
        path.write_text(text)
        if executable:
            path.chmod(0o755)

    def launch(self, system="gb", expected=0):
        result = subprocess.run([self.root / "usr/bin/handheld-retroarch", system, self.rom],
                                env=self.env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)

    def error(self):
        return (self.root / "tmp/handheld/launch-error").read_text()

    def test_quoted_path_and_separate_saves(self):
        self.launch()
        args = json.loads((self.root / "arguments.json").read_text())
        self.assertEqual(args[-1], str(self.rom))
        self.assertFalse((self.root / "INJECTED").exists())
        config = self.root / "tmp/handheld/retroarch-display.cfg"
        self.assertIn('/roms/saves/gb"', config.read_text())
        self.assertIn('video_rotation = "1"', config.read_text())
        self.launch("snes")
        self.assertIn('/roms/saves/snes"', config.read_text())
        self.assertIn('/roms/states/snes"', config.read_text())

    def test_missing_core_rom_and_unknown_system(self):
        self.launch("../invalid", expected=1)
        self.assertIn("not configured", self.error())
        (self.root / "usr/lib/libretro/gambatte_libretro.so").unlink()
        self.launch(expected=1)
        self.assertIn("emulator is missing", self.error())
        self.rom.unlink()
        self.launch(expected=1)
        self.assertIn("game file is missing", self.error())
        self.assertFalse((self.root / "arguments.json").exists())

    def test_required_bios_and_psp_assets(self):
        self.launch("pcenginecd", expected=1)
        self.assertIn("syscard3.pce", self.error())
        self.write("roms/bios/syscard3.pce", "user BIOS")
        self.launch("pcenginecd")
        self.launch("segacd", expected=1)
        self.write("roms/bios/bios_CD_U.bin", "user BIOS")
        self.launch("segacd")
        self.launch("psp")
        assets = self.root / "roms/bios/PPSSPP"
        self.assertTrue(assets.is_symlink())
        assets.unlink()
        assets.mkdir()
        (assets / "compat.ini").write_text("user assets")
        self.launch("psp")
        self.assertEqual((assets / "compat.ini").read_text(), "user assets")

    def test_core_failure_has_displayable_error_and_log(self):
        self.env["CORE_EXIT"] = "3"
        self.launch(expected=1)
        self.assertIn("could not run", self.error())
        self.assertTrue((self.root / "tmp/handheld/retroarch.log").is_file())
        self.env.pop("CORE_EXIT")
        self.launch()
        self.assertFalse((self.root / "tmp/handheld/launch-error").exists())

    def test_assets_on_filesystems_without_symlinks(self):
        self.write("usr/bin/ln", "#!/bin/sh\nexit 1\n", executable=True)
        self.launch("psp")
        assets = self.root / "roms/bios/PPSSPP"
        self.assertFalse(assets.is_symlink())
        self.assertEqual((assets / "compat.ini").read_text(), "fixture")
        (assets / "compat.ini").write_text("user assets")
        self.launch("psp")
        self.assertEqual((assets / "compat.ini").read_text(), "user assets")

    def test_missing_games_card_does_not_create_fallback_saves(self):
        self.write("etc/config/fstab", "configured games card")
        self.write("lib/functions.sh", '''
config_load() { :; }
config_foreach() { "$1" games; }
config_get() { export "$1=$FIXTURE/roms"; }
config_get_bool() { export "$1=1"; }
''')
        self.write("proc/mounts", "")
        self.launch(expected=1)
        self.assertIn("Game storage", self.error())
        self.assertFalse((self.root / "roms/saves").exists())
        self.write("proc/mounts", f"/dev/card {self.root}/roms ext4 rw 0 0\n")
        self.launch()

    def test_low_save_space_prevents_launch(self):
        self.write("usr/bin/df", "#!/bin/sh\necho '/dev/card 100000 99000 1000 99% /roms'\n", executable=True)
        self.launch(expected=1)
        self.assertIn("16 MiB", self.error())
        self.assertFalse((self.root / "arguments.json").exists())
        self.assertFalse(list((self.root / "roms/saves/gb").glob(".save-check.*")))

    def test_service_stop_reaches_running_game_session(self):
        # Model SDL queuing a quit while ES is waiting on its game child.
        self.write("usr/bin/emulationstation", '''#!/bin/sh
trap ':' TERM
printf '%s' "$$" > "$FIXTURE/session-pid"
"$FIXTURE/usr/bin/handheld-retroarch" gb "$TEST_ROM" &
game=$!
wait "$game" || wait "$game"
''', executable=True)
        source = ROOT / "package/games/emulationstation/files/usr/bin/emulationstation-session"
        tail = "child=\n" + source.read_text().split("child=\n", 1)[1]
        tail = tail.replace("/usr/bin/emulationstation", str(self.root / "usr/bin/emulationstation"))
        tail = tail.replace(' < /dev/tty1 > /dev/tty1 2>&1', '').replace('setsid -c', 'setsid')
        self.write("usr/bin/supervisor", "#!/bin/sh\nrotation=0\n" + tail, executable=True)
        env = dict(self.env, WAIT_FOR_STOP="1", TEST_ROM=str(self.rom))
        process = subprocess.Popen(['busybox', 'ash', self.root / 'usr/bin/supervisor'], env=env)
        try:
            deadline = time.monotonic() + 5
            while not (self.root / "ready").exists():
                self.assertIsNone(process.poll())
                if time.monotonic() > deadline: self.fail("Game session did not start")
                time.sleep(0.02)
            process.terminate()
            self.assertEqual(process.wait(timeout=5), 0)
            self.assertEqual((self.root / "flushed").read_text(), "saved")
        finally:
            if process.poll() is None: process.kill(); process.wait()
            pidfile = self.root / "session-pid"
            if pidfile.exists():
                try: os.killpg(int(pidfile.read_text()), signal.SIGKILL)
                except ProcessLookupError: pass
            pidfile = self.root / "emulator-pid"
            if pidfile.exists():
                try: os.kill(int(pidfile.read_text()), signal.SIGKILL)
                except ProcessLookupError: pass

    def test_shutdown_waits_for_emulator_save_flush(self):
        env = dict(self.env, WAIT_FOR_STOP="1")
        process = subprocess.Popen([self.root / "usr/bin/handheld-retroarch", "gb", self.rom], env=env)
        try:
            deadline = time.monotonic() + 5
            while not (self.root / "ready").exists():
                self.assertIsNone(process.poll())
                if time.monotonic() > deadline:
                    self.fail("Emulator did not start")
                time.sleep(0.02)
            process.terminate()
            self.assertEqual(process.wait(timeout=5), 0)
            self.assertEqual((self.root / "flushed").read_text(), "saved")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            pidfile = self.root / "emulator-pid"
            if pidfile.exists():
                try: os.kill(int(pidfile.read_text()), signal.SIGKILL)
                except ProcessLookupError: pass


if __name__ == "__main__":
    unittest.main()
