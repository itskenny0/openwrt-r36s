#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
set -eu
cd "$(dirname "$0")/.."
case "${1:-r36s}" in r36s|all) profile=${1:-r36s} ;; *) echo 'Usage: rk3326-configure.sh [r36s|all]' >&2; exit 2 ;; esac
command -v swig >/dev/null || { echo 'Install the build dependencies listed in docs/BUILD.md (missing swig).' >&2; exit 1; }

./scripts/feeds update -a
# Install the dependency closure we use. Installing every unrelated feed package
# also imports its Kconfig constraints into this firmware configuration.
./scripts/feeds install luci alsa-utils libdrm libexpat libzstd \
	elfutils libudev-zero libsamplerate libusb-1.0 freetype libcurl \
	libidn2 libiconv-full python-mako python-packaging gettext-full \
	exfat-mkfs exfat-fsck libpng libjpeg-turbo libwebp bluez-daemon bluez-utils python-pyelftools python-yaml
cp configs/rk3326.config .config
if [ "$profile" = all ]; then
	printf '\nCONFIG_TARGET_MULTI_PROFILE=y\nCONFIG_TARGET_ALL_PROFILES=y\n' >> .config
fi
make defconfig
python3 scripts/rk3326-check-config.py
