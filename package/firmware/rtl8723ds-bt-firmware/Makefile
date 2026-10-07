# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=rtl8723ds-bt-firmware
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_LICENSE:=LicenseRef-Realtek-Firmware
FIRMWARE_COMMIT:=c9b61eedbc8df1887de29d0de849f580b6a7d9f3
FIRMWARE_URL:=https://raw.githubusercontent.com/ROCKNIX/distribution/$(FIRMWARE_COMMIT)/projects/ROCKNIX/packages/linux-firmware/kernel-firmware/extra-firmware/rtl_bt/

include $(INCLUDE_DIR)/package.mk

define Download/rtl8723ds-bt-fw
  FILE:=rtl8723ds_fw.bin
  URL:=$(FIRMWARE_URL)
  HASH:=19c1bed7a9359b1a021c20f81b525bdebf5067f9021716991d94be9101f76e63
endef
define Download/rtl8723ds-bt-config
  FILE:=rtl8723ds_config.bin
  URL:=$(FIRMWARE_URL)
  HASH:=7d1e18df7654da8f6382520841bb535f2d1246fc8495e3ae652f7b23e820168d
endef
$(eval $(call Download,rtl8723ds-bt-fw))
$(eval $(call Download,rtl8723ds-bt-config))

define Package/rtl8723ds-bt-firmware
  SECTION:=firmware
  CATEGORY:=Firmware
  TITLE:=Realtek RTL8723DS Bluetooth firmware and board configuration
endef

define Build/Compile
endef

define Package/rtl8723ds-bt-firmware/install
	$(INSTALL_DIR) $(1)/lib/firmware/rtl_bt
	$(INSTALL_DATA) $(DL_DIR)/rtl8723ds_fw.bin $(DL_DIR)/rtl8723ds_config.bin $(1)/lib/firmware/rtl_bt/
	$(INSTALL_DIR) $(1)/usr/share/licenses/rtl8723ds-bt-firmware
	$(INSTALL_DATA) ./files/LICENSE $(1)/usr/share/licenses/rtl8723ds-bt-firmware/
endef

$(eval $(call BuildPackage,rtl8723ds-bt-firmware))
