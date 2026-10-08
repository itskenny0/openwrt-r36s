# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=sdl2-image
PKG_VERSION:=2.8.12
PKG_RELEASE:=1
PKG_SOURCE:=SDL2_image-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://github.com/libsdl-org/SDL_image/releases/download/release-$(PKG_VERSION)
PKG_HASH:=393f5efb50536ec13ca4f4affb69cc9966d3c3f969e6c5e701faddf9f9785381
PKG_BUILD_DIR:=$(BUILD_DIR)/SDL2_image-$(PKG_VERSION)
PKG_LICENSE:=Zlib
PKG_LICENSE_FILES:=LICENSE.txt
PKG_BUILD_PARALLEL:=1
CMAKE_INSTALL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

CMAKE_BINARY_SUBDIR:=openwrt-build

define Package/libsdl2-image
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=SDL image decoding for handheld artwork
  DEPENDS:=+libsdl2-rk3326 +libpng +libjpeg-turbo +libwebp
endef

CMAKE_OPTIONS += -DBUILD_SHARED_LIBS=ON -DSDL2IMAGE_INSTALL=ON \
	-DSDL2IMAGE_VENDORED=OFF -DSDL2IMAGE_DEPS_SHARED=OFF -DSDL2IMAGE_STRICT=ON \
	-DSDL2IMAGE_SAMPLES=OFF -DSDL2IMAGE_TESTS=OFF -DSDL2IMAGE_BACKEND_STB=OFF \
	-DSDL2IMAGE_PNG=ON -DSDL2IMAGE_JPG=ON -DSDL2IMAGE_WEBP=ON \
	$(foreach format,AVIF BMP GIF JXL LBM PCX PNM QOI SVG TGA TIF XCF XPM XV,-DSDL2IMAGE_$(format)=OFF)

define Package/libsdl2-image/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libSDL2_image*.so* $(1)/usr/lib/
endef

$(eval $(call BuildPackage,libsdl2-image))
