"""Exercise the shipped shell helpers against a simulated kernel/UCI boundary."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work"
WORK.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location("images", ROOT / "scripts/rk3326-check-images.py")
images = importlib.util.module_from_spec(spec)
spec.loader.exec_module(images)


class GadgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-usb-", dir=WORK)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, FIXTURE=str(self.root))
        self.env["PATH"] = str(self.root / "bin") + os.pathsep + self.env["PATH"]
        for path in ("bin", "var/lock", "sys/class/udc/ff580000.usb", "sys/class/usb_role/dwc2",
                     "sys/kernel/config/usb_gadget/openwrt/os_desc",
                     "sys/kernel/config/usb_gadget/openwrt/functions/rndis.usb1/os_desc/interface.rndis"):
            (self.root / path).mkdir(parents=True)
        self.write("sys/class/usb_role/dwc2/role", "host\n")
        self.write("sys/firmware/devicetree/base/serial-number", "a1b2c3d4\0")
        self.write("proc/mounts", f"configfs {self.root}/sys/kernel/config configfs rw 0 0\n")
        self.write("uci.json", json.dumps({"handheld.usb.mode": "host", "network.lan.ipaddr": "192.168.1.1"}))
        for command in ("sleep", "logger"):
            self.write("bin/" + command, "#!/bin/sh\nexit 0\n", executable=True)
        self.write("bin/uci", '''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ["FIXTURE"])
path = root / "uci.json"
data = json.loads(path.read_text())
args = [x for x in sys.argv[1:] if x != "-q"]
if args[0] == "get":
    if args[1] not in data: sys.exit(1)
    print(data[args[1]])
elif args[0] == "set":
    key, value = args[1].split("=", 1)
    data[key] = value
    path.write_text(json.dumps(data))
elif args[0] == "commit":
    (root / "committed").write_text(args[1])
''', executable=True)
        files = ROOT / "package/system/rk3326-handheld/files"
        for path in ("usr/sbin/handheld-usb", "usr/libexec/handheld-usb-apply"):
            content = (files / path).read_text()
            # Substitute only filesystem roots; execute the original control flow.
            for prefix in ("/sys/", "/proc/", "/etc/", "/var/", "/usr/libexec/"):
                content = content.replace(prefix, str(self.root) + prefix)
            self.write(path, content, executable=True)

    def write(self, path, content, executable=False):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        if executable:
            path.chmod(0o755)

    def run_mode(self, mode, expected=0):
        result = subprocess.run([self.root / "usr/sbin/handheld-usb", mode], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout.strip()

    def read(self, path):
        return (self.root / path).read_text().strip()

    def test_enable_persist_disable(self):
        self.run_mode("gadget")
        self.assertEqual(self.read("sys/class/usb_role/dwc2/role"), "device")
        self.assertEqual(self.read("sys/kernel/config/usb_gadget/openwrt/UDC"), "ff580000.usb")
        self.assertEqual(self.read("committed"), "handheld")
        self.run_mode("status")
        self.run_mode("host")
        self.assertEqual(self.read("sys/class/usb_role/dwc2/role"), "host")
        self.assertEqual(self.read("sys/kernel/config/usb_gadget/openwrt/UDC"), "")
        self.run_mode("status", expected=1)

    def test_missing_controller_rolls_back_without_persisting(self):
        (self.root / "sys/class/udc/ff580000.usb").rmdir()
        self.run_mode("gadget", expected=1)
        self.assertEqual(self.read("sys/class/usb_role/dwc2/role"), "host")
        self.assertFalse((self.root / "committed").exists())
        self.run_mode("status", expected=1)

    def test_repeated_enable_and_incomplete_config_recover(self):
        g = self.root / "sys/kernel/config/usb_gadget/openwrt"
        (g / "configs/c.1").mkdir(parents=True)
        self.run_mode("gadget")
        mac = (g / "functions/ecm.usb0/dev_addr").read_text()
        self.assertTrue((g / "configs/c.1/ecm.usb0").is_symlink())
        self.assertTrue((g / "configs/c.2/rndis.usb1").is_symlink())
        self.assertTrue((g / "os_desc/c.2").is_symlink())
        self.run_mode("gadget")
        self.assertEqual(mac, (g / "functions/ecm.usb0/dev_addr").read_text())
        self.run_mode("host")
        self.run_mode("gadget")

    def test_restore_and_custom_luci_address(self):
        self.write("uci.json", json.dumps({"handheld.usb.mode": "gadget", "network.lan.ipaddr": "192.168.5.1"}))
        self.run_mode("restore")
        self.assertFalse((self.root / "committed").exists())
        self.assertEqual(self.read("sys/class/usb_role/dwc2/role"), "device")
        self.assertEqual(self.run_mode("address"), "192.168.5.1")

    def test_missing_role_switch_and_invalid_mode(self):
        (self.root / "sys/class/usb_role/dwc2/role").unlink()
        self.run_mode("gadget", expected=1)
        self.run_mode("invalid", expected=2)
        self.assertFalse((self.root / "committed").exists())

    def test_upgrade_defaults_preserve_custom_network(self):
        data = {"network.lan.ipaddr": "192.168.5.1", "network.lan.device": "br-lan",
                "network.cfgbridge.name": "br-lan", "system.hostname": "my-console"}
        self.write("uci.json", json.dumps(data))
        self.write("lib/functions.sh", '''
config_load() { :; }
config_foreach() { "$1" cfgbridge; }
config_get() { export "$1=$(uci -q get "network.$2.$3" || true)"; }
''')
        path = "etc/apk/repositories.d/distfeeds.list"
        self.write(path, "https://downloads.openwrt.org/snapshots/targets/rk3326/packages/packages.adb\n")
        source = ROOT / "package/system/rk3326-handheld/files/etc/uci-defaults/90-handheld"
        script = source.read_text().replace("/lib/", str(self.root) + "/lib/")
        script = script.replace("/etc/", str(self.root) + "/etc/")
        self.write("defaults", script, executable=True)
        subprocess.run([self.root / "defaults"], env=self.env, check=True)
        updated = json.loads(self.read("uci.json"))
        self.assertEqual(updated, dict(data, **{"network.cfgbridge.bridge_empty": "1"}))
        self.assertTrue(self.read(path).startswith("# https://"))
        updated["network.cfgbridge.bridge_empty"] = "0"
        self.write("uci.json", json.dumps(updated))
        subprocess.run([self.root / "defaults"], env=self.env, check=True)
        self.assertEqual(json.loads(self.read("uci.json")), updated)


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-image-", dir=WORK)
        self.addCleanup(self.temp.cleanup)
        self.raw = Path(self.temp.name) / "image.raw"
        self.gz = self.raw.with_suffix(".gz")

    def test_gzip_with_fwtool_trailer(self):
        data = b"firmware" * 300000
        compressor = zlib.compressobj(wbits=31)
        self.gz.write_bytes(compressor.compress(data) + compressor.flush() + b"metadata")
        images.unpack_image(self.gz, self.raw)
        self.assertEqual(self.raw.read_bytes(), data)

    def test_truncated_gzip_rejected(self):
        compressor = zlib.compressobj(wbits=31)
        self.gz.write_bytes((compressor.compress(b"firmware" * 100) + compressor.flush())[:-4])
        with self.assertRaisesRegex(ValueError, "Truncated"):
            images.unpack_image(self.gz, self.raw)

    def make_mbr(self, root_start=96):
        mbr = bytearray(512)
        mbr[510:] = b"\x55\xaa"
        for offset, kind, start, size in ((446, 0x0c, 32, 64), (462, 0x83, root_start, 512)):
            mbr[offset + 4] = kind
            struct.pack_into("<II", mbr, offset + 8, start * 2048, size * 2048)
        with self.raw.open("wb") as raw:
            raw.write(mbr)
            raw.truncate((root_start + 512) * images.MIB)

    def test_valid_partition_layout(self):
        self.make_mbr()
        self.assertEqual(images.partitions(self.raw)[1][1], 96 * images.MIB)

    def test_overlapping_partitions_rejected(self):
        self.make_mbr(root_start=80)
        with self.assertRaisesRegex(ValueError, "placement"):
            images.partitions(self.raw)

    def test_truncated_partition_rejected(self):
        self.make_mbr()
        with self.raw.open("r+b") as raw:
            raw.truncate(100 * images.MIB)
        with self.assertRaisesRegex(ValueError, "length"):
            images.partitions(self.raw)


class RotationTests(unittest.TestCase):
    def test_panel_rotation_conventions(self):
        with tempfile.TemporaryDirectory(prefix="test-rotation-", dir=WORK) as temp:
            root = Path(temp)
            property_file = root / "rotation"
            script = root / "rotation.sh"
            original = ROOT / "package/system/rk3326-handheld/files/usr/sbin/handheld-rotation"
            script.write_text(original.read_text().replace(
                "/sys/firmware/devicetree/base/dsi@ff450000/panel@0/rotation", str(property_file)))
            for degrees, ccw, cw in ((0, 0, 0), (90, 1, 3), (180, 2, 2), (270, 3, 1)):
                property_file.write_bytes(struct.pack(">I", degrees))
                for convention, expected in (("ccw", ccw), ("cw", cw)):
                    with self.subTest(degrees=degrees, convention=convention):
                        actual = subprocess.check_output(["sh", script, convention], text=True)
                        self.assertEqual(actual.strip(), str(expected))
            property_file.unlink()
            self.assertEqual(subprocess.check_output(["sh", script], text=True).strip(), "0")


if __name__ == "__main__":
    unittest.main()
