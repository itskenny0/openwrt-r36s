# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=esp8089-firmware
PKG_VERSION:=19
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0
FIRMWARE_COMMIT:=490722a3c9181d6fee6ad75682aaba4afd9d4b24

include $(INCLUDE_DIR)/package.mk

define Download/esp8089-ate
  FILE:=eagle_fw_ate_config_v19.bin
  URL:=https://raw.githubusercontent.com/armbian/firmware/$(FIRMWARE_COMMIT)/
  HASH:=8f2f3f1fe623e1fe0d4aa1376b4bb6a129479cea9bce6374855b4cec19ac1687
endef
define Download/esp8089-first
  FILE:=eagle_fw_first_init_v19.bin
  URL:=https://raw.githubusercontent.com/armbian/firmware/$(FIRMWARE_COMMIT)/
  HASH:=1b8b7f93f40d3c2dd7ab7f3e2d29cd118604249a5926a320163bf358254e4162
endef
define Download/esp8089-second
  FILE:=eagle_fw_second_init_v19.bin
  URL:=https://raw.githubusercontent.com/armbian/firmware/$(FIRMWARE_COMMIT)/
  HASH:=3ac55633c7c9aa2a0025072a597a19550450bf954d63befe789aeef2b25cfd24
endef
$(eval $(call Download,esp8089-ate))
$(eval $(call Download,esp8089-first))
$(eval $(call Download,esp8089-second))

define Package/esp8089-firmware
  SECTION:=firmware
  CATEGORY:=Firmware
  TITLE:=ESP8089 firmware
endef

define Build/Compile
endef

define Package/esp8089-firmware/install
	$(INSTALL_DIR) $(1)/lib/firmware
	$(INSTALL_DATA) $(DL_DIR)/eagle_fw_ate_config_v19.bin \
		$(DL_DIR)/eagle_fw_first_init_v19.bin \
		$(DL_DIR)/eagle_fw_second_init_v19.bin $(1)/lib/firmware/
endef

$(eval $(call BuildPackage,esp8089-firmware))
