# OpenWrt for RK3326 handhelds

OpenWrt with EmulationStation on the R36S and the RK3326 handheld families described by ROCKNIX. The default image is for an **original R36S with Panel 4**.

This is a hardware bring-up port. CI builds and checks the firmware; a passing build does not establish that a particular console boots. See the [hardware test checklist](docs/TESTING.md) before reporting a working device.

- Mainline Linux 6.18 LTS with OpenWrt and ROCKNIX board-support patches.
- OpenWrt's procd, UCI, netifd, firewall, squashfs/overlay root and sysupgrade.
- LuCI preinstalled; USB Ethernet is a persistent EmulationStation setting.
- EmulationStation on SDL2 KMS/DRM, Mesa Panfrost and ALSA.
- RetroArch with eleven cores for classic consoles, PS1, N64, Dreamcast, PSP and arcade games. See the [system list](docs/EMULATORS.md). No games or commercial BIOS files are included.
- Wi-Fi, Bluetooth and USB Ethernet adapter drivers, with networking independent of frontend startup.
- GitHub Actions builds all device profiles and publishes tagged prereleases with checksums and package archives.

## Install

Download the image matching your device from [Releases](https://github.com/itskenny0/openwrt-r36s/releases). For the original R36S Panel 4, choose the file containing `gameconsole_r36s`. Verify it against `SHA256SUMS`, then write the image to a spare microSD card with an image writer that supports `.img.gz`. Writing an image replaces that card's contents. Keep the original card for recovery.

Put the card in the OS/TF1 slot. EmulationStation starts automatically. For other panels and clone hardware, follow [device and panel setup](docs/HARDWARE.md).

In EmulationStation, press **Start → Network Settings → USB Ethernet**, enable the switch and leave the menu to apply it. Connect a data cable from the console's OTG port to your computer. The computer should obtain an address by DHCP. Open **http://192.168.1.1/** for LuCI; **Connect to LuCI** in the same menu shows the configured address. Set a root password on first use. Standard OpenWrt SSH access is also available.

The USB setting defaults to host mode so USB peripherals can be used. Disable USB Ethernet before connecting a Wi-Fi adapter to the same port. Charging-only ports and cables cannot carry Ethernet. Linux/macOS use CDC ECM; the second USB configuration provides RNDIS for Windows. Host driver selection still needs hardware testing.

Copy your games to the matching [system folders](docs/EMULATORS.md) under `/roms` over SSH/SCP, then restart EmulationStation to refresh the list. Select + Start exits RetroArch. Mount a separate games card at `/roms` using **LuCI → System → Mount Points** before copying games. The initial root partition is 512 MiB; it does not automatically fill the SD card.

Use **Start → Quit → Shutdown System** before removing power. Suspend, automatic headphone routing and physical power-button shortcuts are not yet provided by the frontend integration.

## Build and maintain

See [build instructions](docs/BUILD.md), [hardware profiles](docs/HARDWARE.md), [boot tuning and testing](docs/TESTING.md), and [source provenance](docs/UPSTREAM.md). The original OpenWrt introduction is preserved in [README.openwrt.md](README.openwrt.md).

This repository is based on OpenWrt development sources, with feeds locked to commits. It is not an official OpenWrt release. Use the matching release's package archive for kernel modules; modules from unrelated OpenWrt builds will not match this kernel.
