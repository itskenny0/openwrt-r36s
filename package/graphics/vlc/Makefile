# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=vlc
PKG_VERSION:=3.0.23
PKG_RELEASE:=1
PKG_SOURCE:=vlc-$(PKG_VERSION).tar.xz
PKG_SOURCE_URL:=https://download.videolan.org/pub/videolan/vlc/$(PKG_VERSION)/
PKG_HASH:=e891cae6aa3ccda69bf94173d5105cbc55c7a7d9b1d21b9b21666e69eff3e7e0
PKG_LICENSE:=LGPL-2.1-or-later GPL-2.0-or-later
PKG_LICENSE_FILES:=COPYING COPYING.LIB
PKG_INSTALL:=1
PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_BUILD_DEPENDS:=gettext-full/host

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/nls.mk

define Package/libvlc
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=VLC playback engine for EmulationStation previews
  DEPENDS:=+libstdcpp +libpthread +libffmpeg-es +alsa-lib +zlib +libidn2 +libiconv-full $(ICONV_DEPENDS) $(INTL_DEPENDS)
endef

CONFIGURE_ARGS += \
	--disable-lua --disable-qt --disable-skins2 --disable-nls --disable-dbus \
	--disable-xcb --disable-xvideo --disable-wayland --disable-pulse \
	--disable-vdpau --disable-libva --disable-mmal --disable-omxil \
	--disable-a52 --disable-dca --disable-dvbpsi --disable-libmpeg2 \
	--disable-mad --disable-samplerate --disable-shout --disable-vorbis \
	--disable-sout --disable-vlm --disable-chromecast --disable-live555 \
	--disable-dvdread --disable-dvdnav --disable-bluray --disable-vcd \
	--disable-libcddb --disable-smbclient --disable-sftp --disable-upnp \
	--disable-notify --disable-taglib --disable-secret --disable-gnutls \
	--disable-archive --disable-mtp --disable-vnc --disable-chromaprint \
	--disable-projectm --disable-goom --disable-opencv --disable-freerdp \
	--disable-svg --disable-fluidsynth --disable-jack --disable-lirc \
	--disable-udev --disable-libgcrypt --disable-dc1394 --disable-dv1394 \
	--disable-sdl-image --disable-vpx --disable-theora --disable-speex \
	--disable-faad --disable-schroedinger --disable-opus --disable-dav1d \
	--disable-libplacebo --disable-aribsub \
	--disable-v4l2 --disable-linsys --disable-screen --disable-decklink \
	--disable-png --disable-jpeg --disable-flac --disable-ogg --disable-mpg123 \
	--disable-ncurses --disable-freetype --disable-fontconfig --disable-harfbuzz \
	--disable-dsm --disable-nfs --disable-smb2 --disable-srt \
	--disable-addonmanagermodules \
	--disable-gl --disable-egl --disable-gles2 \
	--enable-avcodec --enable-swscale --enable-alsa --enable-run-as-root
CONFIGURE_VARS += ac_cv_func_newlocale=no
# Cross-link the utilities against the just-built core without a runtime rpath.
TARGET_LDFLAGS += -Wl,-rpath-link=$(PKG_BUILD_DIR)/src/.libs

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr
	$(CP) $(PKG_INSTALL_DIR)/usr/include $(1)/usr/
	$(CP) $(PKG_INSTALL_DIR)/usr/lib $(1)/usr/
endef

define Package/libvlc/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libvlc*.so* $(1)/usr/lib/
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/vlc $(1)/usr/lib/
	find $(1)/usr/lib/vlc -name '*.la' -delete
endef

$(eval $(call BuildPackage,libvlc))
