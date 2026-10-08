# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=rk3326-handheld
PKG_RELEASE:=2
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/rk3326-handheld
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=RK3326 handheld integration
  DEPENDS:=@TARGET_rk3326 +uci +ubus +procd +alsa-utils +dropbear +dnsmasq +uhttpd audio-support video-support input-support
endef

define Package/rk3326-handheld/conffiles
/etc/config/handheld
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) ./src/. $(PKG_BUILD_DIR)/
endef

define Build/Compile
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_CPPFLAGS) -Wall -Wextra -Werror \
		-o $(PKG_BUILD_DIR)/handheld-controls $(PKG_BUILD_DIR)/handheld-controls.c $(TARGET_LDFLAGS)
endef

define Package/rk3326-handheld/install
	$(CP) ./files/. $(1)/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/handheld-controls $(1)/usr/sbin/
endef

$(eval $(call BuildPackage,rk3326-handheld))
