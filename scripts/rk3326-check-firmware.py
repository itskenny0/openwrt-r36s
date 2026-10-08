#!/usr/bin/env python3
"""Check firmware actually requested by the installed networking modules."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
rootfs = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build_dir/target-aarch64_cortex-a35_musl/root-rk3326'
modules = {path.stem: path for path in (rootfs / 'lib/modules').glob('*/*.ko')}
required_modules = {
    'rtl8xxxu', 'r8723bs', 'rtw88_8723cs', 'rtw88_8723ds', 'rtw88_8723du',
    'rtw88_8821cs', 'rtw88_8821cu', 'rtw88_8822bs', 'rtw88_8822cs',
    'rtw88_8821au', 'rtw88_8812au', 'rtw88_8814au', 'rtw88_8822bu', 'rtw88_8822cu',
    'mt7601u', 'mt76x0u', 'mt76x2u', 'esp8089', 'r8152', 'btrtl',
}
errors = [f'Missing driver: {name}' for name in sorted(required_modules - modules.keys())]
firmware = {
    'regulatory.db', 'rtl_bt/rtl8723ds_fw.bin', 'rtl_bt/rtl8723ds_config.bin',
    'rtl_bt/rtl8761bu_fw.bin', 'rtl_bt/rtl8761bu_config.bin',
    'eagle_fw_first_init_v19.bin', 'eagle_fw_second_init_v19.bin', 'eagle_fw_ate_config_v19.bin',
}
for name, path in modules.items():
    if name.startswith(('rtl8xxxu', 'rtw88_', 'r8723bs', 'mt76', 'r8152')):
        # OpenWrt omits MODULE_FIRMWARE metadata. Read the compiled request
        # strings, including the chip-specific alternatives, from the ELF.
        firmware.update(value.decode().rstrip('\0') for value in re.findall(
            rb'(?:[a-z0-9_-]+/)?[a-zA-Z0-9_.-]+\.(?:bin|fw)\x00', path.read_bytes()))
# Upstream declares this unshipped image for a dormant enable_bluetooth branch.
# RTL8723BU Wi-Fi uses rtl8723bu_nic.bin; this is not a Bluetooth support claim.
firmware.discard('rtlwifi/rtl8723bu_bt.bin')
for name in sorted(firmware):
    path = rootfs / 'lib/firmware' / name
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f'Missing firmware: {name}')
if errors:
    sys.exit('\n'.join(errors))
print(f'Checked {len(required_modules)} networking drivers and {len(firmware)} firmware files, including symlink targets.')
