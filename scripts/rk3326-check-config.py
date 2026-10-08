#!/usr/bin/env python3
"""Fail if Kconfig silently drops a required part of the handheld image."""
from pathlib import Path
import sys

config = dict(line.split("=", 1) for line in Path(".config").read_text().splitlines()
              if line.startswith("CONFIG_") and "=" in line)
required = [
    "TARGET_rk3326", "TARGET_rk3326_generic", "TARGET_ROOTFS_SQUASHFS", "PACKAGE_luci", "PACKAGE_e2fsprogs",
    "IMAGEOPT", "PREINITOPT",
    "PACKAGE_rk3326-handheld", "PACKAGE_emulationstation", "PACKAGE_retroarch",
    "PACKAGE_libretro-gambatte", "PACKAGE_libsdl2-image", "PACKAGE_libjpeg-turbo", "PACKAGE_libwebp", "PACKAGE_libmesa-rk3326", "PACKAGE_libsdl2-rk3326",
    "PACKAGE_trusted-firmware-a-rk3326", "PACKAGE_uboot-rk3326-legacy",
    "PACKAGE_uboot-rk3326-modern", "PACKAGE_kmod-bluetooth",
    "PACKAGE_kmod-btusb", "PACKAGE_kmod-btsdio", "PACKAGE_kmod-hci-uart-rtl",
    "PACKAGE_rtl8723ds-bt-firmware", "PACKAGE_kmod-rtw88-8723ds",
    "PACKAGE_kmod-usb-net-rtl8152", "PACKAGE_kmod-usb-net-asix",
    "PACKAGE_kmod-rtl8xxxu", "PACKAGE_kmod-rtw88-8821cu",
    "PACKAGE_kmod-rtw88-8723du", "PACKAGE_kmod-mt7601u", "PACKAGE_kmod-mt76x0u", "PACKAGE_kmod-mt76x2u",
    "PACKAGE_kmod-usb-net-asix-ax88179", "PACKAGE_kmod-usb-net-cdc-ether", "PACKAGE_kmod-usb-net-cdc-ncm",
    "PACKAGE_dropbear", "PACKAGE_dnsmasq", "PACKAGE_uhttpd", "PACKAGE_wifi-scripts", "PACKAGE_firewall4",
    "PACKAGE_kmod-brcmfmac", "PACKAGE_kmod-esp8089", "BRCMFMAC_SDIO", "PACKAGE_wpad-basic-mbedtls",
]
missing = [f"CONFIG_{name}=y" for name in required if config.get(f"CONFIG_{name}") != "y"]
for package in Path("package/games").glob("libretro-*/Makefile"):
    name = "CONFIG_PACKAGE_" + package.parent.name
    if config.get(name) != "y":
        missing.append(name + "=y")
if config.get("CONFIG_TARGET_PREINIT_TIMEOUT") != "0":
    missing.append("CONFIG_TARGET_PREINIT_TIMEOUT=0")
if missing:
    sys.exit("Required configuration missing:\n" + "\n".join(missing))
print("Required handheld packages and networking drivers are selected.")
