# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=uboot-rk3326-legacy
PKG_VERSION:=2492a3e467e332e2350d987234ce6123700b3392
PKG_SOURCE:=uboot-rk3326-legacy-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/ROCKNIX/hardkernel-uboot/tar.gz/$(PKG_VERSION)?
PKG_HASH:=d8b358f20394ff1c901af989d0a5b7740f46708bd93ff714459d7bc3794a72f8
PKG_BUILD_DIR:=$(BUILD_DIR)/hardkernel-uboot-$(PKG_VERSION)
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-or-later
PKG_BUILD_DEPENDS:=rkbin
PKG_BUILD_PARALLEL:=1
PKG_FLAGS:=nonshared
PKG_TARGETS:=bin

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
  SECTION:=boot
  CATEGORY:=Boot Loaders
  TITLE:=RK3326 legacy bootloader
  DEPENDS:=@TARGET_rk3326 +trusted-firmware-a-rk3326
endef

define Build/Prepare
	$(call Build/Prepare/Default)
	$(CP) ./files/. $(PKG_BUILD_DIR)/
endef

UBOOT_FLAGS:=ARCH=arm CROSS_COMPILE=$(TARGET_CROSS) HOSTCC="$(HOSTCC)" \
	HOSTLDFLAGS="$(HOST_LDFLAGS)" KCFLAGS="-Wno-error=unused-but-set-variable" HOSTCFLAGS="$(HOST_CFLAGS) -fcommon -Wno-deprecated-declarations"

define Build/Configure
	$(MAKE) -C $(PKG_BUILD_DIR) $(UBOOT_FLAGS) rocknix_rk3326_defconfig
endef

define Build/Compile
	+$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) $(UBOOT_FLAGS) all
	$(TOPDIR)/scripts/rk3326-pack-uboot.sh $(PKG_BUILD_DIR) $(STAGING_DIR_IMAGE)/rk3326
endef

define Build/InstallDev
	$(INSTALL_DIR) $(STAGING_DIR_IMAGE)
	$(CP) $(PKG_BUILD_DIR)/uboot.bin $(STAGING_DIR_IMAGE)/rk3326-legacy.bin
endef

define Package/$(PKG_NAME)/install
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
