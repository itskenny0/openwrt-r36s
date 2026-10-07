# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/image.mk

# Favor decompression speed on Cortex-A35 over maximum flash density.
SQUASHFSCOMP := zstd -Xcompression-level 3

DEVICE_VARS += RK3326_BOOTLOADER RK3326_DTB

define Build/rk3326-boot
	rm -rf $@.boot
	mkdir -p $@.boot/dtbs $@.boot/overlays
	$(CP) $(IMAGE_KERNEL) $@.boot/Image
	$(foreach dtb,$(DEVICE_DTS),$(CP) $(KDIR)/image-$(dtb).dtb $@.boot/dtbs/$(notdir $(dtb)).dtb;)
	sed 's/@DTB@/$(RK3326_DTB)/g' boot.cmd > $@.boot/boot.cmd
	mkimage -A arm -O linux -T script -C none -d $@.boot/boot.cmd $@.boot/boot.scr
	echo '# fdtfile=$(RK3326_DTB).dtb' > $@.boot/boot.env
	echo '# overlay=mipi-panel.dtbo' >> $@.boot/boot.env
	find $@.boot -exec touch -h -d @$(SOURCE_DATE_EPOCH) {} +
endef

define Build/rk3326-image
	$(SCRIPT_DIR)/gen_rk3326_image.sh $@ \
		$(CONFIG_TARGET_KERNEL_PARTSIZE) $@.boot \
		$(CONFIG_TARGET_ROOTFS_PARTSIZE) $(IMAGE_ROOTFS) \
		$(STAGING_DIR_IMAGE)/rk3326-$(RK3326_BOOTLOADER).bin
endef

RK3326_DTBS := $(notdir $(patsubst %.dts,%,$(wildcard ../files/arch/arm64/boot/dts/rockchip/*.dts)))

define Device/Default
  PROFILES := Default
  KERNEL := kernel-bin
  KERNEL_NAME := Image
  DEVICE_DTS_DIR := $(DTS_DIR)/rockchip
  DEVICE_DTS := $(RK3326_DTBS)
  IMAGES := sysupgrade.img.gz
  IMAGE/sysupgrade.img.gz := rk3326-boot | rk3326-image | gzip | append-metadata
endef

include devices.mk

$(eval $(call BuildImage))
