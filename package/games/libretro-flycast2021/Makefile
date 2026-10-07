# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-flycast2021
PKG_VERSION:=2026.10.07
PKG_RELEASE:=1
PKG_SOURCE_VERSION:=603814c9f73b773c455d9a497f389d2f93a257fd
PKG_SOURCE:=flycast2021-$(PKG_SOURCE_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/metallic77/flycast/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_HASH:=8aa94bdd669bab05a10ff03c8a977eccd41a30063271da3f81a7a50b1a72f4ca
PKG_BUILD_DIR:=$(BUILD_DIR)/flycast-$(PKG_SOURCE_VERSION)
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=LICENSE
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libretro-flycast2021
  SECTION:=games
  CATEGORY:=Games
  TITLE:=Flycast 2021 Dreamcast and Naomi core
  DEPENDS:=@TARGET_rk3326 +libstdcpp +libmesa-rk3326 +zlib
endef

define Build/Configure
endef

define Build/Compile
	+CFLAGS="$(TARGET_CFLAGS) $(TARGET_CPPFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS) $(TARGET_CPPFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) platform=unix \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" CC_AS="$(TARGET_CC) -c -fPIC" \
		ARCH=aarch64 WITH_DYNAREC=arm64 FORCE_GLES=1 HAVE_GL3=0 HAVE_CORE=0 HAVE_VULKAN=0 HAVE_OPENMP=0 HAVE_LTCG=0 HAVE_GENERIC_JIT=0 HAVE_CDROM=0 GIT_VERSION="$(PKG_SOURCE_VERSION)"
endef

define Package/libretro-flycast2021/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-flycast2021
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/flycast_libretro.so $(1)/usr/lib/libretro/flycast2021_libretro.so
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/LICENSE $(1)/usr/share/licenses/libretro-flycast2021/
endef

$(eval $(call BuildPackage,libretro-flycast2021))
