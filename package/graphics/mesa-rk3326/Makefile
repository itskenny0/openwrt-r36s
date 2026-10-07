# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=mesa-rk3326
PKG_VERSION:=24.3.4
PKG_RELEASE:=2
PKG_SOURCE:=mesa-$(PKG_VERSION).tar.xz
PKG_SOURCE_URL:=https://archive.mesa3d.org/
PKG_HASH:=e641ae27191d387599219694560d221b7feaa91c900bcec46bf444218ed66025
PKG_BUILD_DIR:=$(BUILD_DIR)/mesa-$(PKG_VERSION)
PKG_LICENSE:=MIT BSD-3-Clause
PKG_LICENSE_FILES:=docs/license.rst
PKG_BUILD_DEPENDS:=python-mako/host python-packaging/host python-yaml/host
PKG_INSTALL:=1
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
MESON_USE_STAGING_PYTHON:=1
include $(INCLUDE_DIR)/meson.mk

MESON_VARS += PYTHONPATH="$(HOST_PYTHON3PATH)"
MESON_ARGS += \
	-Ddefault_library=shared \
	-Dgallium-drivers=panfrost,softpipe -Dvulkan-drivers= -Dplatforms= \
	-Dllvm=disabled -Dshared-llvm=disabled -Dglx=disabled -Dglvnd=disabled \
	-Dopengl=true -Dgles1=enabled -Dgles2=enabled -Degl=enabled -Dgbm=enabled \
	-Dgallium-vdpau=disabled -Dgallium-va=disabled -Dgallium-xa=disabled \
	-Dgallium-nine=false -Dgallium-opencl=disabled -Dgallium-rusticl=false \
	-Dvideo-codecs= -Dbuild-tests=false -Dtools= -Dvalgrind=disabled \
	-Dlibunwind=disabled -Dlmsensors=disabled

define Package/libmesa-rk3326
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Mesa Panfrost for RK3326 handhelds
  DEPENDS:=@TARGET_rk3326 +libstdcpp +libdrm +libexpat +zlib +libzstd +libelf accel-support
  PROVIDES:=libmesa
endef

define Build/InstallDev
	$(CP) $(PKG_INSTALL_DIR)/usr/. $(1)/usr/
endef

define Package/libmesa-rk3326/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/*.so* $(1)/usr/lib/
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/gbm $(1)/usr/lib/
endef

$(eval $(call BuildPackage,libmesa-rk3326))
