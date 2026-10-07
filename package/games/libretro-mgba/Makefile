# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-mgba
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=e31759b24e7a4e3899285ff720d7b573ac328ae7
PKG_SOURCE:=mgba-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/mgba/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=396d749cce8fe3358b29cbb1db479b1816a151bd688ee45b1d241503cbc40243
PKG_BUILD_DIR:=$(BUILD_DIR)/mgba-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=MPL-2.0
PKG_LICENSE_FILES:=LICENSE
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

define Package/libretro-mgba
  SECTION:=games
  CATEGORY:=Games
  TITLE:=mGBA Game Boy Advance core
  DEPENDS:=@TARGET_rk3326 +libstdcpp
endef

CMAKE_OPTIONS += -DLIBMGBA_ONLY=ON -DBUILD_LIBRETRO=ON -DSKIP_LIBRARY=ON -DBUILD_LTO=OFF

define Package/libretro-mgba/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-mgba
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/mgba_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/LICENSE $(1)/usr/share/licenses/libretro-mgba/
endef

$(eval $(call BuildPackage,libretro-mgba))
