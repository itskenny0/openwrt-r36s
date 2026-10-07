# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-beetle-pce-fast
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=bebe2b13a840fbfd45cb501f5cd0efe01bdb1735
PKG_SOURCE:=beetle-pce-fast-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/beetle-pce-fast-libretro/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=509ce18c6d1191fdea45ce45d2f1224de6b3cd15a8acd53a8816a8ac6a191e35
PKG_BUILD_DIR:=$(BUILD_DIR)/beetle-pce-fast-libretro-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=COPYING
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-beetle-pce-fast
  SECTION:=games
  CATEGORY:=Games
  TITLE:=Beetle PC Engine and CD core
  DEPENDS:=@TARGET_rk3326 +libstdcpp
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR)  platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" LD="$(TARGET_CXX)" \
		HAVE_CDROM=0 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-beetle-pce-fast/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-beetle-pce-fast
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/mednafen_pce_fast_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/$(PKG_LICENSE_FILES) $(1)/usr/share/licenses/libretro-beetle-pce-fast/
endef

$(eval $(call BuildPackage,libretro-beetle-pce-fast))
