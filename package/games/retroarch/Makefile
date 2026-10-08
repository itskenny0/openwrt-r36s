# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=retroarch
PKG_VERSION:=1.22.2
PKG_RELEASE:=5
PKG_SOURCE:=RetroArch-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/libretro/RetroArch/tar.gz/refs/tags/v$(PKG_VERSION)?
PKG_HASH:=245ef18c8fa8fbd9fbb5eb25cf43e17c6aace2f95c1ed99873cbd794012bb232
PKG_BUILD_DIR:=$(BUILD_DIR)/RetroArch-$(PKG_VERSION)
PKG_LICENSE:=GPL-3.0-only
PKG_LICENSE_FILES:=COPYING
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/retroarch
  SECTION:=games
  CATEGORY:=Games
  TITLE:=RetroArch libretro frontend
  DEPENDS:=@TARGET_rk3326 +libstdcpp +alsa-lib +libmesa-rk3326 +libudev-zero +libfreetype +zlib +rk3326-handheld
endef

CONFIGURE_ARGS := --prefix=/usr --host=$(GNU_TARGET_NAME) \
	--enable-opengles --enable-kms --enable-udev --enable-alsa --enable-rgui --enable-freetype \
	--disable-x11 --disable-wayland --disable-vulkan --disable-sdl --disable-sdl2 \
	--disable-pulse --disable-jack --disable-ffmpeg --disable-v4l2 --disable-networking \
	--disable-discord --disable-qt --disable-xmb --disable-ozone --disable-materialui \
	--disable-builtinmbedtls --disable-ssl --disable-cdrom

MAKE_FLAGS += CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" STRIP="$(TARGET_CROSS)strip"
CONFIGURE_VARS += PKG_CONF_PATH="$(STAGING_DIR_HOST)/bin/pkg-config"

define Package/retroarch/conffiles
/etc/retroarch.cfg
/etc/retroarch-core-options.cfg
endef

define Package/retroarch/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/retroarch $(1)/usr/bin/
	$(INSTALL_BIN) ./files/handheld-retroarch ./files/handheld-game-dirs $(1)/usr/bin/
	$(INSTALL_CONF) ./files/retroarch.cfg $(1)/etc/
	$(INSTALL_CONF) ./files/retroarch-core-options.cfg $(1)/etc/
	$(INSTALL_DIR) $(1)/usr/share/retroarch/autoconfig
	$(INSTALL_DATA) ./files/autoconfig/*.cfg $(1)/usr/share/retroarch/autoconfig/
	$(INSTALL_DATA) ./files/systems.tsv $(1)/usr/share/retroarch/
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_DATA) ./files/retroarch.keep $(1)/lib/upgrade/keep.d/retroarch
endef

$(eval $(call BuildPackage,retroarch))
