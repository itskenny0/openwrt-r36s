# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=ffmpeg-es
PKG_VERSION:=7.1.1
PKG_RELEASE:=1
PKG_SOURCE:=ffmpeg-$(PKG_VERSION).tar.xz
PKG_SOURCE_URL:=https://ffmpeg.org/releases/
PKG_HASH:=733984395e0dbbe5c046abda2dc49a5544e7e0e1e2366bba849222ae9e3a03b1
PKG_BUILD_DIR:=$(BUILD_DIR)/ffmpeg-$(PKG_VERSION)
PKG_LICENSE:=LGPL-2.1-or-later
PKG_LICENSE_FILES:=COPYING.LGPLv2.1
PKG_INSTALL:=1
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libffmpeg-es
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=FFmpeg playback libraries for EmulationStation
  DEPENDS:=+zlib +libpthread
  CONFLICTS:=libffmpeg libffmpeg-mini
endef

CONFIGURE_ARGS := --prefix=/usr --target-os=linux --arch=aarch64 \
	--enable-cross-compile --cross-prefix=$(TARGET_CROSS) \
	--cc="$(TARGET_CC)" --cxx="$(TARGET_CXX)" --pkg-config=$(STAGING_DIR_HOST)/bin/pkg-config \
	--extra-cflags="$(TARGET_CFLAGS) $(TARGET_CPPFLAGS)" --extra-ldflags="$(TARGET_LDFLAGS)" \
	--disable-autodetect --disable-static --enable-shared --enable-pic \
	--disable-programs --disable-doc --disable-debug --disable-everything \
	--enable-avcodec --enable-avformat --enable-avutil --enable-swscale --enable-swresample \
	--enable-decoder=h264,mpeg4,mpeg2video,mjpeg,png,vp8,vp9,aac,mp3,vorbis,flac,pcm_s16le \
	--enable-demuxer=mov,matroska,avi,ogg,mp3,wav,image2 \
	--enable-parser=h264,mpeg4video,mpegaudio,aac,vp8,vp9 \
	--enable-protocol=file --enable-zlib --enable-pthreads --disable-avdevice --disable-avfilter

# FFmpeg's linker rules pass compiler-driver options, not raw ld arguments.
MAKE_FLAGS += LD="$(TARGET_CC)"

define Build/InstallDev
	$(CP) $(PKG_INSTALL_DIR)/usr/. $(1)/usr/
	$(SED) 's,^libdir=/usr,libdir=$(STAGING_DIR)/usr,;s,^includedir=/usr,includedir=$(STAGING_DIR)/usr,' $(1)/usr/lib/pkgconfig/libav*.pc $(1)/usr/lib/pkgconfig/libsw*.pc
endef

define Package/libffmpeg-es/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/*.so* $(1)/usr/lib/
endef

$(eval $(call BuildPackage,libffmpeg-es))
