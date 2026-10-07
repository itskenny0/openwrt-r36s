# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-snes9x
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=890b5d445538fe790aa3add3d5702c80f551e0ae
PKG_SOURCE:=snes9x-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/snes9x/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=fcc32b536d3e7b1def0d15489917dd043d5e1d9636de8af7851c48e771276613
PKG_BUILD_DIR:=$(BUILD_DIR)/snes9x-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=LicenseRef-Snes9x
PKG_LICENSE_FILES:=LICENSE
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-snes9x
  SECTION:=games
  CATEGORY:=Games
  TITLE:=Snes9x Super Nintendo core
  DEPENDS:=@TARGET_rk3326 +libstdcpp
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -C $(PKG_BUILD_DIR)/libretro platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" LD="$(TARGET_CXX)" \
		 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-snes9x/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-snes9x
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libretro/snes9x_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/$(PKG_LICENSE_FILES) $(1)/usr/share/licenses/libretro-snes9x/
endef

$(eval $(call BuildPackage,libretro-snes9x))
