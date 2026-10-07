#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
set -eu
image=$1
boot_mb=$2
boot_dir=$3
root_mb=$4
root_image=$5
loader=$6

# The first partition starts at 32 MiB, beyond the Rockchip bootloader slots.
rm -f "$image" "$image.fat"
layout=$(ptgen -o "$image" -h 16 -s 63 -l 32768 -t c -p "${boot_mb}m" -t 83 -p "${root_mb}m")
# ptgen returns four whitespace-separated byte counts.
# shellcheck disable=SC2086
set -- $layout
[ "$#" -eq 4 ]
boot_offset=$1
boot_size=$2
root_offset=$3
root_size=$4
test "$(stat -c %s "$loader")" -le "$((boot_offset - 32768))"
test "$(stat -c %s "$root_image")" -le "$root_size"
truncate -s "$((root_offset + root_size))" "$image"
trap 'rm -f "$image.fat"' EXIT
mkfs.fat --invariant -F 32 -n OPENWRT -C "$image.fat" "$((boot_size / 1024))"

copy_dir() {
	# OpenWrt build hosts provide dash or bash; both support recursive locals.
	# shellcheck disable=SC3043
	local entry name
	for entry in "$1"/*; do
		[ -e "$entry" ] || continue
		name=${entry##*/}
		if [ -d "$entry" ]; then
			mmd -i "$image.fat" "::$2$name"
			copy_dir "$entry" "$2$name/"
		else
			mcopy -m -i "$image.fat" "$entry" "::$2$name"
		fi
	done
}
LC_ALL=C copy_dir "$boot_dir" /
dd if="$loader" of="$image" bs=512 seek=64 conv=notrunc status=none
dd if="$image.fat" of="$image" bs=512 seek="$((boot_offset / 512))" conv=notrunc status=none
dd if="$root_image" of="$image" bs=512 seek="$((root_offset / 512))" conv=notrunc status=none
