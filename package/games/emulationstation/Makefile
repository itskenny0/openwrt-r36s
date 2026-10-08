# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=emulationstation
PKG_VERSION:=2026.07.03
PKG_RELEASE:=4
PKG_SOURCE_VERSION:=1071b8358b316ebda837933150db949bda90495e
PKG_SOURCE:=emulationstation-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/RetroPie/EmulationStation/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=8520004e85f73ef700a366688b54b7e6b8dbb604bae9134d6a0530615b5d90f7
PKG_BUILD_DIR:=$(BUILD_DIR)/EmulationStation-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=MIT
PKG_LICENSE_FILES:=LICENSE.md
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

define Download/pugixml
  FILE:=pugixml-ee86beb30e4973f5feffe3ce63bfa4fbadf72f38.tar.gz
  URL:=https://codeload.github.com/zeux/pugixml/tar.gz/ee86beb30e4973f5feffe3ce63bfa4fbadf72f38?
  HASH:=51c102d4187fac99daa38af281b0772c5e6c586f65004cdc63f8f2e011a21492
endef
$(eval $(call Download,pugixml))

define Download/rapidjson
  FILE:=rapidjson-24b5e7a8b27f42fa16b96fc70aade9106cf7102f.tar.gz
  URL:=https://codeload.github.com/Tencent/rapidjson/tar.gz/24b5e7a8b27f42fa16b96fc70aade9106cf7102f?
  HASH:=2d2601a82d2d3b7e143a3c8d43ef616671391034bc46891a9816b79cf2d3e7a8
endef
$(eval $(call Download,rapidjson))

define Package/emulationstation
  SECTION:=games
  CATEGORY:=Games
  TITLE:=EmulationStation handheld frontend
  DEPENDS:=@TARGET_rk3326 +libstdcpp +libsdl2-rk3326 +libmesa-rk3326 +libsdl2-image +libvlc +libcurl +libfreetype +alsa-lib +rk3326-handheld
endef

define Package/emulationstation/conffiles
/etc/emulationstation/es_systems.cfg
endef

define Build/Prepare
	$(call Build/Prepare/Default)
	tar -xzf $(DL_DIR)/pugixml-ee86beb30e4973f5feffe3ce63bfa4fbadf72f38.tar.gz --strip-components=1 -C $(PKG_BUILD_DIR)/external/pugixml
	mkdir -p $(PKG_BUILD_DIR)/external/rapidjson
	tar -xzf $(DL_DIR)/rapidjson-24b5e7a8b27f42fa16b96fc70aade9106cf7102f.tar.gz --strip-components=1 -C $(PKG_BUILD_DIR)/external/rapidjson
endef

CMAKE_OPTIONS += -DGLES=ON -DCEC=OFF -DOMX=OFF -DRPI=OFF \
	-DRAPIDJSON_INCLUDE_DIRS=$(PKG_BUILD_DIR)/external/rapidjson/include

define Package/emulationstation/install
	$(CP) ./files/. $(1)/
	$(INSTALL_DIR) $(1)/usr/bin $(1)/usr/share/emulationstation/resources
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/emulationstation $(1)/usr/bin/
	$(CP) $(PKG_BUILD_DIR)/resources/. $(1)/usr/share/emulationstation/resources/
endef

$(eval $(call BuildPackage,emulationstation))
