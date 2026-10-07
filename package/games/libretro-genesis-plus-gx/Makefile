# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-genesis-plus-gx
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=b7e79b3641eb2e322c5ba29903352e115887e83c
PKG_SOURCE:=genesis-plus-gx-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/Genesis-Plus-GX/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=5e240e3c9e2cfae0dada87650005c289ed80e31c77c524945fc2c521f787455c
PKG_BUILD_DIR:=$(BUILD_DIR)/Genesis-Plus-GX-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=LicenseRef-Genesis-Plus-GX
PKG_LICENSE_FILES:=LICENSE.txt
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-genesis-plus-gx
  SECTION:=games
  CATEGORY:=Games
  TITLE:=Genesis Plus GX Sega console cores
  DEPENDS:=@TARGET_rk3326 +libstdcpp
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS) -DALIGN_LONG" CXXFLAGS="$(TARGET_CXXFLAGS) -DALIGN_LONG" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -f Makefile.libretro platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" LD="$(TARGET_CXX)" \
		HAVE_CDROM=0 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-genesis-plus-gx/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-genesis-plus-gx
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/genesis_plus_gx_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/$(PKG_LICENSE_FILES) $(1)/usr/share/licenses/libretro-genesis-plus-gx/
endef

$(eval $(call BuildPackage,libretro-genesis-plus-gx))
