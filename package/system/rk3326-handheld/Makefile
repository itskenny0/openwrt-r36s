# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=rk3326-handheld
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/rk3326-handheld
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=RK3326 handheld integration
  DEPENDS:=@TARGET_rk3326 +uci +ubus +procd +alsa-utils audio-support video-support input-support
endef

define Package/rk3326-handheld/conffiles
/etc/config/handheld
endef

define Build/Compile
endef

define Package/rk3326-handheld/install
	$(CP) ./files/. $(1)/
endef

$(eval $(call BuildPackage,rk3326-handheld))
