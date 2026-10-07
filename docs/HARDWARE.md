# Hardware profiles

The scope follows the RK3326 device trees in [ROCKNIX's pinned device list](https://github.com/ROCKNIX/distribution/blob/c9b61eedbc8df1887de29d0de849f580b6a7d9f3/projects/ROCKNIX/config.xml), plus its GameForce Chi tree and an original R36S Panel 4 preset. The table describes **build coverage**, not hardware certification. All boards currently require physical validation with this OpenWrt port.

| Image profile | Device | Default DTB | Bootloader |
| --- | --- | --- | --- |
| `gameconsole_r36s` | Original R36S, Panel 4 | `rk3326-gameconsole-r36s-panel4` | Legacy |
| `gameconsole_r33s` | R33S | `rk3326-gameconsole-r33s` | Legacy |
| `gameconsole_eeclone` | K36 / EE clone family | `rk3326-gameconsole-eeclone` | Modern, UART2 |
| `gameconsole_eeclone-uart5` | EE clones wired for UART5 | `rk3326-gameconsole-eeclone` | Modern, UART5 |
| `anbernic_rg351m` | RG351P / RG351M | `rk3326-anbernic-rg351m` | Legacy |
| `anbernic_rg351v` | RG351V | `rk3326-anbernic-rg351v` | Legacy |
| `hardkernel_odroid-go2` | ODROID Go Advance | `rk3326-odroid-go2` | Legacy |
| `hardkernel_odroid-go2-v11` | ODROID Go Advance Black Edition | `rk3326-odroid-go2-v11` | Legacy |
| `hardkernel_odroid-go3` | ODROID Go Super | `rk3326-odroid-go3` | Legacy |
| `powkiddy_rgb10` | RGB10 | `rk3326-powkiddy-rgb10` | Legacy |
| `powkiddy_rgb10x` | RGB10X | `rk3326-powkiddy-rgb10x` | Modern |
| `powkiddy_rgb20s` | RGB20S | `rk3326-powkiddy-rgb20s` | Modern |
| `magicx_xu10` | XU10 | `rk3326-magicx-xu10` | Legacy |
| `magicx_xu10-modern` | XU10, alternative bootloader | `rk3326-magicx-xu10` | Modern |
| `magicx_xu-mini-m` | XU Mini M | `rk3326-magicx-xu-mini-m` | Modern |
| `batlexp_g350` | G350 | `rk3326-batlexp-g350` | Modern |
| `gkd_pixel2` | GKD Pixel 2 / PX30S | `rk3326s-gkd-pixel2` | Modern |
| `gameforce_chi` | GameForce Chi | `rk3326-gameforce-chi` | Legacy |

Board support includes ROCKNIX's input drivers, RK817 audio/power, display panels, DWC2 role-switch fixes and PX30S support. The graphics stack uses upstream Panfrost with the mainline GPU operating points. Boot firmware includes Rockchip binary DDR initialization and BL31; the Linux kernel itself is mainline LTS with board patches.

## Original R36S panels

The default `gameconsole_r36s` image embeds the Panel 4 initialization sequence. It needs no panel overlay. For the standard R35S/R36S panel, edit `boot.env` on the FAT partition:

```ini
fdtfile=rk3326-gameconsole-r36s.dtb
```

For another panel, place a compatible ROCKNIX **generic-DSI** overlay in `overlays/` on that partition, then use:

```ini
fdtfile=rk3326-gameconsole-r36s.dtb
overlay=mipi-panel.dtbo
```

All DTBs are compiled with symbols for overlays. A missing or invalid requested overlay stops the boot script rather than passing a damaged device tree to Linux. The display rotation property is passed to EmulationStation automatically.

## K36 / EE clones

These are not original R36S boards. Their panel, controller wiring, amplifier and UART can differ between units. As in [ROCKNIX's clone documentation](https://rocknix.org/devices/unbranded/EE-clones/), retain the **stock DTB from your own console**. A generic image alone does not describe every clone.

The pinned upstream converter is included in `scripts/panel/`. On your computer, with the checkout as the current directory:

```sh
python3 -m venv .work/panel-venv
.work/panel-venv/bin/pip install --require-hashes -r scripts/panel/requirements.txt
.work/panel-venv/bin/python scripts/panel/rocknix_dtbo.py stock.dtb -o .work/mipi-panel.dtbo
```

Copy the result to `overlays/mipi-panel.dtbo` on the boot partition and set `overlay=mipi-panel.dtbo` in `boot.env`. Use the UART5 image for stock hardware using UART5; both the DDR firmware and U-Boot are adjusted. The converter accepts upstream correction flags, for example `LSi-HPi`, between the stock filename and `-o`; use them only when the corresponding hardware needs inversion. This port does not scan or modify an internal eMMC to extract configuration.

A stock vendor-kernel DTB cannot be substituted directly for a mainline DTB. The converter extracts selected configuration into an overlay for the mainline tree.

## Networking

USB host and device mode share the DWC2 port. USB Ethernet enables configfs ECM/RNDIS functions, binds the controller and bridges `usb0`/`usb1` into OpenWrt LAN. Disabling it unbinds the gadget and restores host mode. A failed transition restores the previous mode without saving the failed selection. Service startup restores the saved UCI mode.

Wi-Fi and Bluetooth drivers remain modular, so unused adapters do not delay the display. Included USB Ethernet families cover RTL8152, ASIX/AX88179 and CDC Ethernet/NCM. Included Wi-Fi families cover rtl8xxxu, rtw88 8821CU/8723DU/8723DS, mt7601u, mt76x0u/mt76x2u, brcmfmac SDIO and the ROCKNIX ESP8089 driver. Bluetooth includes USB, SDIO and UART transport drivers, including the Chi's RTL8723DS firmware and UART protocol. Additional networking drivers can be selected in the normal OpenWrt build configuration. This does not imply every clone's wireless chip has mainline driver support.
