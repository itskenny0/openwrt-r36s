OpenWrt firmware for RK3326 handhelds, with EmulationStation, Panfrost, LuCI and a persistent USB Ethernet menu setting. The original R36S image defaults to Panel 4.

This revision hardens upgrades against corrupt images and failed writes, forwards shutdown to running games without duplicate signals that interrupt save flushing, protects saves when a games card is missing, and adds persistent brightness/volume, volume buttons, automatic headphone routing and a two-second power hold for shutdown. Artwork decoding now uses SDL2_image with maintained PNG/JPEG/WebP libraries and bounded image dimensions. Hardware validation of these controls is pending.

USB Ethernet enables SSH, DHCP and LuCI. Fresh installations use `192.168.77.1`; upgrades retain the previous LAN address. USB Wi-Fi client provisioning is documented in `NETWORKING.md`.

The firmware includes eleven RetroArch cores for classic consoles, PS1, N64, Dreamcast, PSP and arcade games, with system folders, separate saves, bundled PSP support assets and visible launch errors. Read the attached `EMULATORS.md` for formats, BIOS requirements and controls.

CI checks all device images, loads every core, executes original test programs on seven classic-console cores, drives the rendered frontend through USB, brightness, volume and game launch/save/reload/error flows, and checks DHCP assignment and SSH on a virtual USB link. N64, Dreamcast, PSP and arcade game compatibility and performance still need beta testing. Physical boot, panel, input, audio and USB tests are required for each board. Read `TESTING.md` and the repository's hardware setup instructions before testing. EE clones require an overlay derived from their stock DTB.

Choose the matching device image, verify `SHA256SUMS` and write it to a spare OS card. Keep the stock card for recovery. No games or BIOS files are bundled. ROMs and saves on the root partition are not retained by sysupgrade's configuration backup.

The release includes source/feed pins, build configuration, package manifests and the matching package archive. All release payloads have GitHub build attestations. Linux is mainline 6.18 LTS with OpenWrt and ROCKNIX board patches; boot firmware uses Rockchip's DDR/BL31 components.
