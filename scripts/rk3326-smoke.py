#!/usr/bin/env python3
"""Run built ARM64 programs against their target libraries under QEMU."""
import os
import importlib.util
from pathlib import Path
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[1]
stage = ROOT / "staging_dir/target-aarch64_cortex-a35_musl"
rootfs = ROOT / "build_dir/target-aarch64_cortex-a35_musl/root-rk3326"
preinit = (rootfs / "lib/preinit/00_preinit.conf").read_text().splitlines()
if "fs_failsafe_wait_timeout=0" not in preinit:
    raise SystemExit("Packaged preinit must not impose a failsafe countdown")
for path in ("etc/rc.d/S25emulationstation", "etc/rc.d/S26usb-gadget",
             "www/cgi-bin/luci", "usr/libexec/handheld-usb-apply"):
    if not (rootfs / path).exists():
        raise SystemExit(f"Missing runtime integration: {path}")
work = ROOT / ".work/smoke"
(work / "home").mkdir(parents=True, exist_ok=True)
compiler, = ROOT.glob("staging_dir/toolchain-*/bin/aarch64-openwrt-linux-musl-gcc")
header, = ROOT.glob("build_dir/target-*/gambatte-libretro-*/libgambatte/libretro-common/include")
env = dict(os.environ, STAGING_DIR=str(stage))
spec = importlib.util.spec_from_file_location("roms", ROOT / "tests/runtime/roms.py")
roms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roms)
library_path = ":".join(str(rootfs / path) for path in ("lib", "usr/lib", "usr/lib/libretro"))
qemu = ["qemu-aarch64", "-L", str(rootfs), "-E", "LD_LIBRARY_PATH=" + library_path,
        "-E", "HOME=" + str(work / "home")]


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, env=env, check=True, timeout=120)


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


# A generated 1x1 RGB image exercises FreeImage's decoder without external assets.
(work / "pixel.png").write_bytes(
    b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    + chunk(b"IDAT", zlib.compress(b"\x00\x11\x22\x33")) + chunk(b"IEND", b""))
for name, libraries in (("freeimage", ["-lfreeimage"]), ("libretro", ["-ldl"]),
                        ("graphics", ["-lSDL2", "-lGLESv2"]),
                        ("media", ["-lavcodec", "-lavformat", "-lavutil"])):
    # Link against development files; image stripping removes ELF section tables.
    # Run against the final root filesystem to verify the shipped payload.
    run(compiler, "-I" + str(stage / "usr/include"), "-I" + str(header),
        ROOT / f"tests/runtime/{name}.c", "-L" + str(stage / "usr/lib"),
        "-L" + str(stage / "root-rk3326/usr/lib/libretro"), "-Wl,-rpath-link," + str(stage / "usr/lib"),
        *libraries, "-o", work / name)
    args = [work / name]
    if name == "freeimage":
        args.append(work / "pixel.png")
        run(*qemu, *args)
    elif name == "media":
        run(*qemu, *args)
    elif name == "graphics":
        run(*qemu, "-E", "SDL_VIDEODRIVER=offscreen", "-E", "EGL_PLATFORM=surfaceless",
            "-E", "GALLIUM_DRIVER=softpipe", "-E", "LIBGL_DRIVERS_PATH=" + str(rootfs / "usr/lib/dri"), *args)
# Check every installed system resolves to a loadable target core.
registry = rootfs / "usr/share/retroarch/systems.tsv"
cores = {line.split("|")[4] for line in registry.read_text().splitlines()
         if line and not line.startswith("#")}
for core in sorted(cores):
    run(*qemu, work / "libretro", rootfs / f"usr/lib/libretro/{core}_libretro.so")
for core, rom in roms.write_roms(work / "roms").items():
    args = [work / "libretro", rootfs / f"usr/lib/libretro/{core}_libretro.so", rom]
    if core in {"gambatte", "fceumm", "snes9x", "mgba"}:
        args.append("sram-marker")
    run(*qemu, *args)
run(*qemu, rootfs / "usr/bin/retroarch", "--version")
run(*qemu, rootfs / "usr/bin/emulationstation", "--help")
print("ARM64 image decoding, core loading, console frames/audio/save states and frontend startup checks passed.")
