# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=libretro-ppsspp
PKG_VERSION:=1.20.4
PKG_RELEASE:=1
PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/hrydgard/ppsspp.git
PKG_SOURCE_VERSION:=fa50bb1976065c4f8b1b47af227d367fe9771555
PKG_SOURCE_SUBDIR:=ppsspp-$(PKG_VERSION)
PKG_SOURCE:=ppsspp-$(PKG_VERSION)-$(PKG_SOURCE_VERSION).tar.zst
PKG_MIRROR_HASH:=030b59567836fb83b65b17868ef99ff0115a11c49c985b9351a7b22de9067b2f
PKG_SOURCE_SUBMODULES:=libretro/libretro-common ext/armips ext/glslang ext/SPIRV-Cross \
	ext/rapidjson ext/miniupnp ext/zstd ext/cpu_features ext/rcheevos ext/naett \
	ext/libchdr ext/lua ext/nanosvg ext/aemu_postoffice ext/OpenXR-SDK
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=LICENSE.TXT
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

define Package/libretro-ppsspp
  SECTION:=games
  CATEGORY:=Games
  TITLE:=PPSSPP PlayStation Portable core
  DEPENDS:=@TARGET_rk3326 +libstdcpp +libmesa-rk3326 +libffmpeg-es +libcurl +libpng +libzstd +zlib
endef

CMAKE_OPTIONS += -DLIBRETRO=ON -DFORCED_CPU=aarch64 \
	-DUSING_GLES2=ON -DUSING_EGL=OFF -DUSING_FBDEV=ON \
	-DVULKAN=OFF -DUSE_VULKAN_DISPLAY_KHR=OFF -DUSING_X11_VULKAN=OFF -DOPENXR=OFF \
	-DUSE_WAYLAND_WSI=OFF -DCMAKE_DISABLE_FIND_PACKAGE_X11=TRUE \
	-DUSE_SYSTEM_FFMPEG=ON -DUSE_SYSTEM_ZSTD=ON -DUSE_SYSTEM_LIBPNG=ON \
	-DUSING_QT_UI=OFF -DUNITTEST=OFF -DSIMULATOR=OFF -DHEADLESS=OFF -DUSE_DISCORD=OFF \
	-DCMAKE_POSITION_INDEPENDENT_CODE=ON

define Build/Prepare
	$(call Build/Prepare/Default)
	printf '%s\n' 'const char *PPSSPP_GIT_VERSION = "v$(PKG_VERSION)";' \
		'#define PPSSPP_GIT_VERSION_NO_UPDATE 1' > $(PKG_BUILD_DIR)/git-version.cpp
endef

define Package/libretro-ppsspp/install
	$(INSTALL_DIR) $(1)/usr/lib/libretro $(1)/usr/share/licenses/libretro-ppsspp
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/lib/ppsspp_libretro.so $(1)/usr/lib/libretro/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/LICENSE.TXT $(1)/usr/share/licenses/libretro-ppsspp/
	$(INSTALL_DIR) $(1)/usr/share/retroarch/system/PPSSPP
	$(CP) $(PKG_BUILD_DIR)/assets/. $(1)/usr/share/retroarch/system/PPSSPP/
endef

$(eval $(call BuildPackage,libretro-ppsspp))
