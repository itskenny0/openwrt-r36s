# Sources and licensing

The OpenWrt source tree and its history are retained. Board files and package sources keep their original copyright notices and licenses. New integration code uses GPL-2.0-only unless a file says otherwise. Each dependency's own license continues to apply; the repository is not a relicensing of the combined firmware.

| Component | Pinned source / basis | Use |
| --- | --- | --- |
| OpenWrt | [`0ab51fb9c13fd88d5eba565cd3fd22b7b9a18bbf`](https://github.com/openwrt/openwrt/commit/0ab51fb9c13fd88d5eba565cd3fd22b7b9a18bbf) | Build system, userspace, kernel integration |
| Linux | 6.18 LTS, exact revision/hash in `target/linux/generic/kernel-6.18` | Mainline kernel plus OpenWrt and board patches |
| ROCKNIX | [`c9b61eedbc8df1887de29d0de849f580b6a7d9f3`](https://github.com/ROCKNIX/distribution/tree/c9b61eedbc8df1887de29d0de849f580b6a7d9f3) | RK3326 DTS, display/input/PX30S/DWC2 patches, bootloader configurations, controller mappings |
| ROCKNIX joypad | [`d02ed13aae08113f6f9e0e9d699cb29bb3450fa2`](https://github.com/ROCKNIX/rocknix-joypad/tree/d02ed13aae08113f6f9e0e9d699cb29bb3450fa2) | Polled handheld input drivers |
| EmulationStation | [RetroPie `1071b8358b316ebda837933150db949bda90495e`](https://github.com/RetroPie/EmulationStation/tree/1071b8358b316ebda837933150db949bda90495e) | MIT-licensed frontend; native OpenWrt network menu patch |
| dArkOSen integration reference | [`5b713abc41be66ba00a3fc70028be240f814f81d`](https://github.com/djparentx/EmulationStation-fcamod-dArkOS-EN/tree/5b713abc41be66ba00a3fc70028be240f814f81d) | Studied native network menu/system-helper pattern; adapted the integration to UCI/procd |
| Panel converter | [`stolen/overlay_server`, `04e5e55b82d30c5c03d060f44cb6d7cd8840f531`](https://github.com/stolen/overlay_server/tree/04e5e55b82d30c5c03d060f44cb6d7cd8840f531) | MIT-licensed `scripts/panel/rocknix_dtbo.py`; license alongside it |
| R36S Panel 4 data | [`stolen/rnix` panel overlays](https://github.com/stolen/rnix/releases/tag/panel_overlays), asset `mipi-panel.dtbo.r36s-panel4` | Generic-DSI panel description embedded in the Panel 4 DTS |
| Legacy U-Boot | [ROCKNIX/hardkernel-uboot `2492a3e467e332e2350d987234ce6123700b3392`](https://github.com/ROCKNIX/hardkernel-uboot/tree/2492a3e467e332e2350d987234ce6123700b3392) | Original board bootloader, patched boot command and host-build fixes |
| Modern U-Boot | [2025.10](https://source.denx.de/u-boot/u-boot/-/tree/v2025.10) | ROCKNIX handheld config, eMMC support and optional UART5 |
| Rockchip rkbin | [`74213af1e952c4683d2e35952507133b61394862`](https://github.com/rockchip-linux/rkbin/tree/74213af1e952c4683d2e35952507133b61394862) | DDR 2.11, miniloader 1.40, BL31 1.34 and packaging tools; upstream binary redistribution terms |

Package Makefiles record the versions, source URLs, SHA-256 hashes and licenses for Mesa, SDL2, FreeImage, VLC, FFmpeg, RetroArch, the emulator cores and EmulationStation's bundled dependencies. Classic-console, arcade, N64 and Dreamcast core revisions follow the pinned ROCKNIX tree; PPSSPP is pinned to v1.20.4 with its required submodules. Core licenses are installed in `/usr/share/licenses`; Snes9x, Genesis Plus GX and FinalBurn Neo have their own redistribution terms. SDL2's OpenWrt packaging is derived from the pinned video feed. The other feed revisions are recorded in `feeds.conf.default` and copied into each release as `feeds.lock`.

The ROCKNIX board patches are adapted to Linux 6.18 APIs. In particular, input-polldev and the older GPIO helper API are carried for the handheld drivers. ESP8089 is packaged against OpenWrt mac80211 backports. The Chi's RTL8723DS Bluetooth firmware and board configuration are pinned to the same ROCKNIX revision; the firmware license is installed alongside them. The vendor Mali driver and vendor GPU overclock table are not used. Panfrost uses the mainline GPU configuration.

To obtain corresponding sources for a release, check out its tag, run `./scripts/rk3326-configure.sh all`, then `make download`. The sources are placed in `dl/`; all local modifications, configuration files and build recipes are in the tagged repository. License files from upstream archives remain in their respective sources. No game ROMs or commercial BIOS files are distributed.
