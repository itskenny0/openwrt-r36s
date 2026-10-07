# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=gambatte
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=d9d6cd06382d1ced30de34d56d3609452323dab1
PKG_SOURCE:=gambatte-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/gambatte-libretro/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=bd39cd38662135d17e221a7fd34baf2908a40065ade16edf2e8d1168b21b921e
PKG_BUILD_DIR:=$(BUILD_DIR)/gambatte-libretro-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=GPL-2.0-only
PKG_LICENSE_FILES:=COPYING
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-gambatte
  SECTION:=games
  CATEGORY:=Games
  TITLE:=Gambatte Game Boy / Game Boy Color core
  DEPENDS:=+libstdcpp
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" $(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -f Makefile.libretro platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" \
		LDFLAGS="$(TARGET_LDFLAGS)"
endef

define Package/libretro-gambatte/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/gambatte_libretro.so $(1)/usr/lib/libretro/
endef

$(eval $(call BuildPackage,libretro-gambatte))
