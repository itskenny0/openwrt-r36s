# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=freeimage
PKG_VERSION:=3.18.0
PKG_RELEASE:=1
PKG_SOURCE:=FreeImage3180.zip
PKG_SOURCE_URL:=@SF/freeimage
PKG_HASH:=f41379682f9ada94ea7b34fe86bf9ee00935a3147be41b6569c9605a53e438fd
PKG_BUILD_DIR:=$(BUILD_DIR)/FreeImage
PKG_LICENSE:=GPL-2.0-or-later
PKG_LICENSE_FILES:=license-gplv2.txt license-gplv3.txt
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libfreeimage
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=FreeImage image decoding library
  DEPENDS:=+libstdcpp
endef

TARGET_CFLAGS += -fPIC -fexceptions -fvisibility=hidden -DPNG_ARM_NEON_OPT=0 -Wno-implicit-function-declaration
TARGET_CXXFLAGS += -fPIC -fexceptions -fvisibility=hidden -std=c++11 -Wno-narrowing

MAKE_FLAGS += \
	CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" AR="$(TARGET_AR)" \
	CFLAGS="$(TARGET_CFLAGS) $(TARGET_CPPFLAGS) -DOPJ_STATIC -DNO_LCMS -DDISABLE_PERF_MEASUREMENT -D__ANSI__" \
	CXXFLAGS="$(TARGET_CXXFLAGS) $(TARGET_CPPFLAGS) -D__ANSI__" \
	LDFLAGS="$(TARGET_LDFLAGS)"

define Build/Compile
	+$(MAKE) $(PKG_JOBS) -C $(PKG_BUILD_DIR) -f Makefile.gnu $(MAKE_FLAGS)
endef

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/include $(1)/usr/lib
	$(CP) $(PKG_BUILD_DIR)/Source/FreeImage.h $(1)/usr/include/
	$(CP) $(PKG_BUILD_DIR)/libfreeimage-3.18.0.so $(1)/usr/lib/
	$(LN) libfreeimage-3.18.0.so $(1)/usr/lib/libfreeimage.so.3
	$(LN) libfreeimage.so.3 $(1)/usr/lib/libfreeimage.so
endef

define Package/libfreeimage/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_BUILD_DIR)/libfreeimage-3.18.0.so $(1)/usr/lib/
	$(LN) libfreeimage-3.18.0.so $(1)/usr/lib/libfreeimage.so.3
endef

$(eval $(call BuildPackage,libfreeimage))
