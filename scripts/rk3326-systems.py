#!/usr/bin/env python3
"""Generate the default EmulationStation list from the installed core registry."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
registry = ROOT / "package/games/retroarch/files/systems.tsv"
destination = ROOT / "package/games/emulationstation/files/etc/emulationstation/es_systems.cfg"
systems = ET.Element("systemList")


def add(**fields):
    system = ET.SubElement(systems, "system")
    for key, value in fields.items():
        ET.SubElement(system, key).text = value


add(name="tools", fullname="OpenWrt", path="/usr/share/handheld/tools", extension=".sh",
    command="sh %ROM%", platform="ignore", theme="openwrt")
for line in registry.read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    ident, name, platform, theme, core, extensions = line.split("|")
    suffixes = ["." + ext for ext in extensions.split()]
    add(name=ident, fullname=name, path="/roms/" + ident,
        extension=" ".join(suffixes + [ext.upper() for ext in suffixes]),
        command=f"/usr/bin/handheld-retroarch {ident} %ROM%", platform=platform, theme=theme)
ET.indent(systems, space="  ")
output = '<?xml version="1.0"?>\n' + ET.tostring(systems, encoding="unicode") + "\n"
if "--check" in sys.argv:
    if destination.read_text() != output:
        sys.exit("Run python3 scripts/rk3326-systems.py to update es_systems.cfg")
else:
    destination.write_text(output)
