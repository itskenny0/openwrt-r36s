# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-pcsx-rearmed
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=da2cb8ecd17fd0932ab6d94774c0522beebce6e3
PKG_SOURCE:=pcsx_rearmed-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/pcsx_rearmed/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=ff191a349aa88b7156f2c40ae32b7144884eec921542f07508d88715105d175e
PKG_BUILD_DIR:=$(BUILD_DIR)/pcsx_rearmed-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=COPYING
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-pcsx-rearmed
  SECTION:=games
  CATEGORY:=Games
  TITLE:=PCSX ReARMed PlayStation core
  DEPENDS:=@TARGET_rk3326 +libstdcpp
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -f Makefile.libretro platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" LD="$(TARGET_CROSS)ld" \
		ARCH=aarch64 DYNAREC=ari64 BUILTIN_GPU=neon HAVE_NEON_ASM=0 HAVE_PHYSICAL_CDROM=0 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-pcsx-rearmed/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-pcsx-rearmed
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/pcsx_rearmed_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/$(PKG_LICENSE_FILES) $(1)/usr/share/licenses/libretro-pcsx-rearmed/
endef

$(eval $(call BuildPackage,libretro-pcsx-rearmed))
