# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-fbneo
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=f3b774987e009d07f1322ebc4910532ed5b8c808
PKG_SOURCE:=fbneo-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/FBNeo/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=48e35bf75aa76200fb2bc64fa12d25606e0b7ebe3dcc41c37a641c33f93601d5
PKG_BUILD_DIR:=$(BUILD_DIR)/FBNeo-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=LicenseRef-FBNeo
PKG_LICENSE_FILES:=LICENSE.md
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-fbneo
  SECTION:=games
  CATEGORY:=Games
  TITLE:=FinalBurn Neo arcade core
  DEPENDS:=@TARGET_rk3326 +libstdcpp +zlib
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -C $(PKG_BUILD_DIR)/src/burner/libretro platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" LD="$(TARGET_CXX)" \
		profile=performance USE_CYCLONE=0 EXTERNAL_ZLIB=1 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-fbneo/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-fbneo
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/src/burner/libretro/fbneo_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DIR) $(1)/usr/share/retroarch/system/fbneo
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/metadata/hiscore.dat $(1)/usr/share/retroarch/system/fbneo/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/$(PKG_LICENSE_FILES) $(1)/usr/share/licenses/libretro-fbneo/
endef

$(eval $(call BuildPackage,libretro-fbneo))
