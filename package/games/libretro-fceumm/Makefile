# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-fceumm
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=236ccdfc911e84c60fea6b9d0699c2d440a8de14
PKG_SOURCE:=fceumm-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/libretro-fceumm/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=dd002cde9b5271979e0394bb9e696bd37e149ced473ff1e3629cc7fed502381f
PKG_BUILD_DIR:=$(BUILD_DIR)/libretro-fceumm-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=Copying
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-fceumm
  SECTION:=games
  CATEGORY:=Games
  TITLE:=FCEUmm NES core
  DEPENDS:=@TARGET_rk3326 +libstdcpp
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -f Makefile.libretro platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" LD="$(TARGET_CXX)" \
		 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-fceumm/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-fceumm
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/fceumm_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/$(PKG_LICENSE_FILES) $(1)/usr/share/licenses/libretro-fceumm/
endef

$(eval $(call BuildPackage,libretro-fceumm))
