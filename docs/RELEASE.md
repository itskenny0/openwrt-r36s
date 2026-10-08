OpenWrt firmware for RK3326 handhelds, with EmulationStation, Panfrost, LuCI and a persistent USB Ethernet menu setting. The original R36S image defaults to Panel 4.

This beta includes eleven RetroArch cores for classic consoles, PS1, N64, Dreamcast, PSP and arcade games, with system folders, separate saves, bundled PSP support assets and visible launch errors. Read the attached `EMULATORS.md` for formats, BIOS requirements and controls.

CI checks all device images, loads every core, executes original test programs on seven classic-console cores, and drives the rendered frontend through USB settings and game launch/save/reload/error flows. N64, Dreamcast, PSP and arcade game compatibility and performance still need beta testing. Physical boot, panel, input, audio and USB tests are required for each board. Read `TESTING.md` and the repository's hardware setup instructions before testing. EE clones require an overlay derived from their stock DTB.

Choose the matching device image, verify `SHA256SUMS` and write it to a spare OS card. Keep the stock card for recovery. No games or BIOS files are bundled. ROMs and saves on the root partition are not retained by sysupgrade's configuration backup.

The release includes source/feed pins, build configuration, package manifests and the matching package archive. Linux is mainline 6.18 LTS with OpenWrt and ROCKNIX board patches; boot firmware uses Rockchip's DDR/BL31 components.
