# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=uboot-rk3326-modern
PKG_VERSION:=2025.10
PKG_SOURCE:=u-boot-$(PKG_VERSION).tar.bz2
PKG_SOURCE_URL:=https://ftp.denx.de/pub/u-boot/
PKG_HASH:=b4f032848e56cc8f213ad59f9132c084dbbb632bc29176d024e58220e0efdf4a
PKG_BUILD_DIR:=$(BUILD_DIR)/u-boot-rk3326-modern/u-boot-$(PKG_VERSION)
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-or-later
PKG_BUILD_DEPENDS:=rkbin python3/host python-setuptools/host python-pyelftools/host
PKG_BUILD_PARALLEL:=1
PKG_FLAGS:=nonshared
PKG_TARGETS:=bin

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
  SECTION:=boot
  CATEGORY:=Boot Loaders
  TITLE:=RK3326 modern bootloader
  DEPENDS:=@TARGET_rk3326 +trusted-firmware-a-rk3326
endef

define Build/Prepare
	$(call Build/Prepare/Default)
	$(CP) ./files/. $(PKG_BUILD_DIR)/
endef

UBOOT_FLAGS:=ARCH=arm CROSS_COMPILE=$(TARGET_CROSS) HOSTCC="$(HOSTCC)" \
	HOSTLDFLAGS="$(HOST_LDFLAGS)" HOSTCFLAGS="$(HOST_CFLAGS)" \
	PYTHON3=$(STAGING_DIR_HOSTPKG)/bin/python3

define Build/Configure
	$(MAKE) -C $(PKG_BUILD_DIR) $(UBOOT_FLAGS) rk3326-handheld_defconfig
endef

define Build/Compile
	+$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) $(UBOOT_FLAGS) u-boot-dtb.bin
	$(TOPDIR)/scripts/rk3326-pack-uboot.sh $(PKG_BUILD_DIR) $(STAGING_DIR_IMAGE)/rk3326
	mv $(PKG_BUILD_DIR)/uboot.bin $(PKG_BUILD_DIR)/uboot-default.bin
	$(PKG_BUILD_DIR)/scripts/config --file $(PKG_BUILD_DIR)/.config --set-val CONFIG_DEBUG_UART_BASE 0xFF178000
	$(PKG_BUILD_DIR)/scripts/config --file $(PKG_BUILD_DIR)/.config --set-str CONFIG_DEVICE_TREE_INCLUDES "rk3326-odroid-go2-emmc.dtsi rk3326-odroid-go2-uart5.dtsi"
	+$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) $(UBOOT_FLAGS) u-boot-dtb.bin
	$(TOPDIR)/scripts/rk3326-pack-uboot.sh $(PKG_BUILD_DIR) $(STAGING_DIR_IMAGE)/rk3326 rk3326_ddr_uart5.bin
endef

define Build/InstallDev
	$(INSTALL_DIR) $(STAGING_DIR_IMAGE)
	$(CP) $(PKG_BUILD_DIR)/uboot-default.bin $(STAGING_DIR_IMAGE)/rk3326-modern.bin
	$(CP) $(PKG_BUILD_DIR)/uboot.bin $(STAGING_DIR_IMAGE)/rk3326-modern-uart5.bin
endef

define Package/$(PKG_NAME)/install
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
