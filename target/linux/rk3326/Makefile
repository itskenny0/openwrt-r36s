# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

ARCH:=aarch64
BOARD:=rk3326
BOARDNAME:=Rockchip RK3326 handhelds
SUBTARGETS:=generic
CPU_TYPE:=cortex-a35
FEATURES:=ext4 squashfs fpu usb usbgadget audio display gpio dt-overlay rootfs-part boot-part
KERNEL_PATCHVER:=6.18

include $(INCLUDE_DIR)/target.mk

DEFAULT_PACKAGES += audio-support video-support input-support accel-support e2fsprogs partx-utils block-mount luci rk3326-handheld emulationstation retroarch libretro-gambatte
KERNELNAME:=Image dtbs

$(eval $(call BuildTarget))
