# SPDX-License-Identifier: GPL-2.0-only

define Device/gameconsole_r36s
  DEVICE_VENDOR := Game Console
  DEVICE_MODEL := R36S Panel 4
  RK3326_DTB := rk3326-gameconsole-r36s-panel4
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := gameconsole,r36s gameconsole,r35s
endef
TARGET_DEVICES += gameconsole_r36s

define Device/gameconsole_r33s
  DEVICE_VENDOR := Game Console
  DEVICE_MODEL := R33S
  RK3326_DTB := rk3326-gameconsole-r33s
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := gameconsole,r33s
endef
TARGET_DEVICES += gameconsole_r33s

define Device/gameconsole_eeclone
  DEVICE_VENDOR := Game Console
  DEVICE_MODEL := K36 / EE clones
  RK3326_DTB := rk3326-gameconsole-eeclone
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
  SUPPORTED_DEVICES := gameconsole,eeclone
endef
TARGET_DEVICES += gameconsole_eeclone

define Device/gameconsole_eeclone-uart5
  $(Device/gameconsole_eeclone)
  DEVICE_VARIANT := UART5
  RK3326_BOOTLOADER := modern-uart5
endef
TARGET_DEVICES += gameconsole_eeclone-uart5

define Device/anbernic_rg351m
  DEVICE_VENDOR := Anbernic
  DEVICE_MODEL := RG351P / RG351M
  RK3326_DTB := rk3326-anbernic-rg351m
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := anbernic,rg351m
endef
TARGET_DEVICES += anbernic_rg351m

define Device/anbernic_rg351v
  DEVICE_VENDOR := Anbernic
  DEVICE_MODEL := RG351V
  RK3326_DTB := rk3326-anbernic-rg351v
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := anbernic,rg351v
endef
TARGET_DEVICES += anbernic_rg351v

define Device/hardkernel_odroid-go2
  DEVICE_VENDOR := Hardkernel
  DEVICE_MODEL := ODROID Go Advance
  RK3326_DTB := rk3326-odroid-go2
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := hardkernel,rk3326-odroid-go2
endef
TARGET_DEVICES += hardkernel_odroid-go2

define Device/hardkernel_odroid-go2-v11
  DEVICE_VENDOR := Hardkernel
  DEVICE_MODEL := ODROID Go Advance Black Edition
  RK3326_DTB := rk3326-odroid-go2-v11
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := hardkernel,rk3326-odroid-go2-v11
endef
TARGET_DEVICES += hardkernel_odroid-go2-v11

define Device/hardkernel_odroid-go3
  DEVICE_VENDOR := Hardkernel
  DEVICE_MODEL := ODROID Go Super
  RK3326_DTB := rk3326-odroid-go3
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := hardkernel,rk3326-odroid-go3
endef
TARGET_DEVICES += hardkernel_odroid-go3

define Device/powkiddy_rgb10
  DEVICE_VENDOR := Powkiddy
  DEVICE_MODEL := RGB10
  RK3326_DTB := rk3326-powkiddy-rgb10
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := powkiddy,rk3326-rgb10
endef
TARGET_DEVICES += powkiddy_rgb10

define Device/powkiddy_rgb10x
  DEVICE_VENDOR := Powkiddy
  DEVICE_MODEL := RGB10X
  RK3326_DTB := rk3326-powkiddy-rgb10x
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
  SUPPORTED_DEVICES := powkiddy,rk3326-rgb10x
endef
TARGET_DEVICES += powkiddy_rgb10x

define Device/powkiddy_rgb20s
  DEVICE_VENDOR := Powkiddy
  DEVICE_MODEL := RGB20S
  RK3326_DTB := rk3326-powkiddy-rgb20s
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
  SUPPORTED_DEVICES := powkiddy,rgb20s
endef
TARGET_DEVICES += powkiddy_rgb20s

define Device/magicx_xu10
  DEVICE_VENDOR := MagicX
  DEVICE_MODEL := XU10
  RK3326_DTB := rk3326-magicx-xu10
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := magicx,xu10
endef
TARGET_DEVICES += magicx_xu10

define Device/magicx_xu10-modern
  $(Device/magicx_xu10)
  DEVICE_VARIANT := Modern bootloader
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
endef
TARGET_DEVICES += magicx_xu10-modern

define Device/magicx_xu-mini-m
  DEVICE_VENDOR := MagicX
  DEVICE_MODEL := XU Mini M
  RK3326_DTB := rk3326-magicx-xu-mini-m
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
  SUPPORTED_DEVICES := magicx,xu-mini-m
endef
TARGET_DEVICES += magicx_xu-mini-m

define Device/batlexp_g350
  DEVICE_VENDOR := BatleXP
  DEVICE_MODEL := G350
  RK3326_DTB := rk3326-batlexp-g350
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
  SUPPORTED_DEVICES := batlexp,g350
endef
TARGET_DEVICES += batlexp_g350

define Device/gkd_pixel2
  DEVICE_VENDOR := GKD
  DEVICE_MODEL := Pixel 2
  RK3326_DTB := rk3326s-gkd-pixel2
  RK3326_BOOTLOADER := modern
  DEVICE_PACKAGES := uboot-rk3326-modern
  SUPPORTED_DEVICES := gamekiddy,gkd-pixel2
endef
TARGET_DEVICES += gkd_pixel2

define Device/gameforce_chi
  DEVICE_VENDOR := GameForce
  DEVICE_MODEL := Chi
  RK3326_DTB := rk3326-gameforce-chi
  RK3326_BOOTLOADER := legacy
  DEVICE_PACKAGES := uboot-rk3326-legacy
  SUPPORTED_DEVICES := gameforce,chi
endef
TARGET_DEVICES += gameforce_chi
