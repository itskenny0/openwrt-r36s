#!/usr/bin/env python3
"""Validate SD image layout and boot payload before publishing firmware."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 * 1024


def unpack_image(source, destination, allow_trailer=True):
    # OpenWrt appends fwtool metadata outside the gzip member.
    decoder = zlib.decompressobj(31)
    with source.open("rb") as src, destination.open("wb") as dst:
        while chunk := src.read(MIB):
            while chunk and not decoder.eof:
                data = decoder.decompress(chunk, MIB)
                # Keep image padding sparse while validating both downloads
                # for every profile. Reads still return the original zeroes.
                if data.strip(b"\0"):
                    dst.write(data)
                else:
                    dst.seek(len(data), 1)
                chunk = decoder.unconsumed_tail
            if decoder.eof:
                if not allow_trailer and (decoder.unused_data or src.read(1)):
                    raise ValueError(f"Unexpected data after gzip image: {source.name}")
                break
        dst.truncate()
    if not decoder.eof:
        raise ValueError(f"Truncated gzip stream: {source.name}")


def partitions(raw):
    with raw.open("rb") as image:
        mbr = image.read(512)
    if len(mbr) != 512 or mbr[510:] != b"\x55\xaa":
        raise ValueError("Missing MBR signature")
    result = []
    for offset in (446, 462):
        kind = mbr[offset + 4]
        start, sectors = struct.unpack_from("<II", mbr, offset + 8)
        result.append((kind, start * 512, sectors * 512))
    boot, root = result
    if boot[0] != 0x0c or root[0] != 0x83:
        raise ValueError("Expected FAT32 boot and Linux root partitions")
    if boot[1] != 32 * MIB or boot[2] < 64 * MIB:
        raise ValueError("Boot partition overlaps firmware or is too small")
    if root[1] < boot[1] + boot[2] or root[2] < 512 * MIB:
        raise ValueError("Invalid root partition placement or size")
    if raw.stat().st_size != root[1] + root[2]:
        raise ValueError("Image length does not match partition table")
    return boot, root


def check_image(source, raw, mcopy, fwtool, dtbs, expected_dtb):
    sdcard = source.name.endswith("-sdcard.img.gz")
    if not sdcard:
        metadata = json.loads(subprocess.check_output([fwtool, "-i", "/dev/stdout", source]))
        if not metadata.get("supported_devices"):
            raise ValueError("Missing sysupgrade compatibility metadata")
    unpack_image(source, raw, allow_trailer=not sdcard)
    boot, root = partitions(raw)
    with raw.open("rb") as image:
        for offset in (32768, 8 * MIB, 12 * MIB):
            image.seek(offset)
            if not any(image.read(512)):
                raise ValueError(f"Empty bootloader slot at {offset}")
        image.seek(root[1])
        if image.read(4) != b"hsqs":
            raise ValueError("Root partition is not squashfs")

    def read_boot(path):
        return subprocess.check_output([mcopy, "-i", f"{raw}@@{boot[1]}", f"::/{path}", "-"])

    kernel = read_boot("Image")
    if kernel[56:60] != b"ARM\x64":
        raise ValueError("Boot kernel is not a raw arm64 Image")
    script = read_boot("boot.scr")
    if script[:4] != b"\x27\x05\x19\x56":
        raise ValueError("Invalid U-Boot script header")
    size, expected_crc = struct.unpack_from(">I", script, 12)[0], struct.unpack_from(">I", script, 24)[0]
    if zlib.crc32(script[64:64 + size]) != expected_crc:
        raise ValueError("Corrupt U-Boot script payload")
    selected = re.search(rb"setenv fdtfile ([\w-]+\.dtb)", script)
    if not selected or selected[1].decode() != expected_dtb:
        raise ValueError(f"Boot script must select {expected_dtb}")
    read_boot("boot.env")
    for dtb in dtbs:
        data = read_boot("dtbs/" + dtb)
        if data[:4] != b"\xd0\x0d\xfe\xed" or struct.unpack_from(">I", data, 4)[0] != len(data):
            raise ValueError(f"Invalid device tree: {dtb}")
    print(f"Validated {source.name}: {selected[1].decode()}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    os.environ["PATH"] = str(ROOT / "staging_dir/host/bin") + os.pathsep + os.environ["PATH"]
    mcopy, fwtool = shutil.which("mcopy"), shutil.which("fwtool")
    if not mcopy or not fwtool:
        parser.error("Build the host mtools and fwtool first")
    devices = (ROOT / "target/linux/rk3326/image/devices.mk").read_text()
    profiles = re.findall(r"^TARGET_DEVICES \+= (.+)$", devices, re.M)
    definitions = dict(re.findall(r"^define Device/([^\n]+)\n(.*?)^endef", devices, re.M | re.S))

    def profile_dtb(profile):
        definition = definitions[profile]
        match = re.search(r"^\s*RK3326_DTB := (\S+)", definition, re.M)
        if match:
            return match[1] + ".dtb"
        parent = re.search(r"\$\(Device/([^\)]+)\)", definition)
        if not parent:
            raise ValueError(f"Missing default DTB for {profile}")
        return profile_dtb(parent[1])

    dtbs = {p.stem + ".dtb" for p in (ROOT / "target/linux/rk3326/files/arch/arm64/boot/dts/rockchip").glob("*.dts")}
    images = sorted(args.directory.glob("*.img.gz"))
    selected_images = {}
    for profile in profiles:
        for kind in ("sdcard", "sysupgrade"):
            matches = [p for p in images if p.name.endswith(f"-{profile}-squashfs-{kind}.img.gz")]
            if len(matches) != 1:
                parser.error(f"Missing {kind} image for profile: {profile}")
            selected_images[matches[0]] = profile_dtb(profile)
    if len(images) != len(selected_images):
        parser.error("Unexpected extra images in release directory")
    workspace = ROOT / ".work"
    workspace.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="image-check-", dir=workspace) as temp:
        raw = Path(temp) / "image.raw"
        for image, dtb in selected_images.items():
            check_image(image, raw, mcopy, fwtool, dtbs, dtb)


if __name__ == "__main__":
    main()
