#!/usr/bin/env python3
"""Check the resolved kernel configuration, not just the input fragment."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
config = dict(line.split("=", 1) for line in path.read_text().splitlines()
              if line.startswith("CONFIG_") and "=" in line)
required = [
    "ARCH_ROCKCHIP", "MMC_DW_ROCKCHIP", "REGULATOR_RK808", "MFD_RK8XX_I2C",
    "DRM_ROCKCHIP", "ROCKCHIP_VOP", "ROCKCHIP_DW_MIPI_DSI", "DRM_PANFROST",
    "DRM_PANEL_GENERIC_DSI", "PHY_ROCKCHIP_INNO_DSIDPHY", "BACKLIGHT_PWM",
    "INPUT_EVDEV", "JOYSTICK_ROCKNIX", "KEYBOARD_ADC", "SND_SOC_RK817",
    "USB_DWC2", "USB_DWC2_DUAL_ROLE", "USB_GADGET", "USB_ROLE_SWITCH",
    "CONFIGFS_FS", "USB_CONFIGFS", "USB_CONFIGFS_ECM", "USB_CONFIGFS_RNDIS",
    "VFAT_FS", "SQUASHFS", "SQUASHFS_ZSTD", "EXT4_FS", "BLK_DEV_LOOP",
]
missing = [f"CONFIG_{name}=y" for name in required if config.get(f"CONFIG_{name}") != "y"]
for name in ("BT", "BT_HCIBTUSB", "BT_HCIBTSDIO", "BT_HCIUART", "BT_HCIUART_RTL"):
    if config.get(f"CONFIG_{name}") not in ("y", "m"):
        missing.append(f"CONFIG_{name} must be enabled for Bluetooth")
for name in ("DEBUG_INFO", "KALLSYMS", "FTRACE", "KASAN", "UBSAN", "KCOV", "LOCKDEP"):
    if config.get(f"CONFIG_{name}") == "y":
        missing.append(f"CONFIG_{name} must be disabled in release builds")
if missing:
    sys.exit("Required kernel configuration missing:\n" + "\n".join(missing))
print("Boot, display, input, audio and USB gadget drivers are built in.")
