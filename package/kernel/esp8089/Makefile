# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=esp8089
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-only
PKG_BUILD_PARALLEL:=1
PKG_FILE_DEPENDS:=$(TOPDIR)/target/linux/rk3326/files/drivers/net/wireless/esp8089
STAMP_CONFIGURED_DEPENDS:=$(STAGING_DIR)/usr/include/mac80211-backport/backport/autoconf.h

include $(INCLUDE_DIR)/package.mk

define KernelPackage/esp8089
  SUBMENU:=Wireless Drivers
  TITLE:=ESP8089 SDIO Wi-Fi for RK3326 handhelds
  DEPENDS:=@TARGET_rk3326 +kmod-mac80211 +kmod-mmc +esp8089-firmware
  FILES:=$(PKG_BUILD_DIR)/esp8089.ko
  AUTOLOAD:=$(call AutoProbe,esp8089)
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(PKG_FILE_DEPENDS)/. $(PKG_BUILD_DIR)/
	$(call Build/Patch)
endef

NOSTDINC_FLAGS:= \
	$(KERNEL_NOSTDINC_FLAGS) \
	-I$(PKG_BUILD_DIR) \
	-I$(STAGING_DIR)/usr/include/mac80211-backport/uapi \
	-I$(STAGING_DIR)/usr/include/mac80211-backport \
	-I$(STAGING_DIR)/usr/include/mac80211/uapi \
	-I$(STAGING_DIR)/usr/include/mac80211 \
	-include backport/autoconf.h -include backport/backport.h

define Build/Compile
	+$(KERNEL_MAKE) $(PKG_JOBS) M="$(PKG_BUILD_DIR)" \
		NOSTDINC_FLAGS="$(NOSTDINC_FLAGS)" CONFIG_ESP8089=m modules
endef

$(eval $(call KernelPackage,esp8089))
