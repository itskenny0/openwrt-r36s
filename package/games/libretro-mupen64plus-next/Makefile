# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-mupen64plus-next
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=f275caf4b2bfa1e6d1c51636746ea793f3d80320
PKG_SOURCE:=mupen64plus-nx-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/mupen64plus-libretro-nx/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=1810b7bbdc4abfdeee8a9f7f99c4a91dab601a228935802317c25a43d7cf9dbb
PKG_BUILD_DIR:=$(BUILD_DIR)/mupen64plus-libretro-nx-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=LICENSE
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-mupen64plus-next
  SECTION:=games
  CATEGORY:=Games
  TITLE:=Mupen64Plus-Next Nintendo 64 core
  DEPENDS:=@TARGET_rk3326 +libstdcpp +libmesa-rk3326 +zlib
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS) $(TARGET_CPPFLAGS) -DHAVE_UNISTD_H" CXXFLAGS="$(TARGET_CXXFLAGS) $(TARGET_CPPFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" CC_AS="$(TARGET_CC)" \
		ARCH=aarch64 WITH_DYNAREC=aarch64 FORCE_GLES3=1 HAVE_PARALLEL_RSP=0 HAVE_PARALLEL_RDP=0 LLE=0 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-mupen64plus-next/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-mupen64plus-next
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/mupen64plus_next_libretro.so $(1)/usr/lib/libretro/mupen64plus_next_libretro.so
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/LICENSE $(1)/usr/share/licenses/libretro-mupen64plus-next/
endef

$(eval $(call BuildPackage,libretro-mupen64plus-next))
