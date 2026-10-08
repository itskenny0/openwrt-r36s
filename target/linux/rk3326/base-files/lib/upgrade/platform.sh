# SPDX-License-Identifier: GPL-2.0-only
REQUIRE_IMAGE_METADATA=1

# The generic stage2 dispatcher ignores hook return codes. A failed destructive
# operation must exit its shell so it cannot announce success and reboot.
rk3326_upgrade_abort() {
	echo "Upgrade stopped: $*" >&2
	exit 1
}

# Strip fwtool's trailer before checking gzip's CRC. Keep the root filesystem
# compressed in RAM: a raw image is too large for these consoles.
rk3326_image_stream() (
	set -o pipefail
	# zcat forks a seamless decompressor and can discard its CRC failure.
	fwtool -q -T -i /dev/null "$1" | busybox gunzip -c
)

# This port ships MBR images. Check the format before the generic partition
# reader, whose invalid-table path can otherwise exit with status zero.
rk3326_partitions() {
	local magic
	magic=$(hexdump -v -s 510 -n 2 -e '2/1 "%02x"' "$1")
	[ "$magic" = 55aa ] || return 1
	rm -f "/tmp/partmap.$2"
	get_partitions "$1" "$2"
	[ -s "/tmp/partmap.$2" ]
}

platform_check_image() (
	local diskdev partdev bytes expected part start size
	set -o pipefail
	if [ "${SAVE_PARTITIONS:-1}" != 1 ] || [ "${UPGRADE_OPT_SAVE_PARTITIONS:-1}" != 1 ]; then
		echo 'Changing the partition table requires writing a full SD image.' >&2
		return 1
	fi
	export_bootdevice && export_partdevice diskdev 0 || return 1
	# Drain the stream so every decompression/checksum error is observed.
	rk3326_image_stream "$1" | { dd of=/tmp/image.bs bs=512 count=1 iflag=fullblock 2>/dev/null && cat >/dev/null; } || return 1
	rk3326_partitions /tmp/image.bs image || return 1
	rk3326_partitions "/dev/$diskdev" bootdisk || return 1
	# Never overwrite an unexpected partition, a resized root or a games card.
	awk 'NR == 1 { if ($1 != 1 || $2 != 65536 || $3 != 131072) exit 1 }
	     NR == 2 { if ($1 != 2 || $2 < 196608 || $2 % 2048 != 0 || $3 <= 0) exit 1 }
	     END { if (NR != 2) exit 1 }' /tmp/partmap.image || return 1
	grep -F -x -v -f /tmp/partmap.bootdisk /tmp/partmap.image >/dev/null && {
		echo 'Partition layout changed. Write a full image to a spare card.' >&2
		return 1
	}
	while read -r part start size; do
		export_partdevice partdev "$part" || return 1
	done < /tmp/partmap.image
	expected=$(awk 'END { printf "%.0f", ($2 + $3) * 512 }' /tmp/partmap.image)
	bytes=$(rk3326_image_stream "$1" | wc -c) || return 1
	[ "$bytes" -eq "$expected" ] || {
		echo 'Image length does not match its partition table.' >&2
		return 1
	}
)

platform_pre_upgrade() {
	local partdev failed=0
	platform_check_image "$1" || rk3326_upgrade_abort 'image or partition validation failed'
	[ -n "$UPGRADE_BACKUP" ] || return 0
	export_bootdevice || rk3326_upgrade_abort 'boot device unavailable'
	export_partdevice partdev 1 || rk3326_upgrade_abort 'boot partition unavailable'
	mkdir -p /tmp/handheld-boot /mnt || rk3326_upgrade_abort 'cannot prepare boot backup'
	mount -o ro,noatime "/dev/$partdev" /mnt || rk3326_upgrade_abort 'cannot mount boot partition'
	if [ -f /mnt/boot.env ]; then cp /mnt/boot.env /tmp/handheld-boot/ || failed=1; fi
	if [ -d /mnt/overlays ]; then cp -R /mnt/overlays /tmp/handheld-boot/ || failed=1; fi
	umount /mnt || failed=1
	[ "$failed" = 0 ] || rk3326_upgrade_abort 'cannot preserve panel configuration'
}

platform_copy_config() {
	local partdev failed=0
	export_bootdevice || rk3326_upgrade_abort 'boot device unavailable'
	export_partdevice partdev 1 || rk3326_upgrade_abort 'boot partition unavailable'
	mount -o rw,noatime "/dev/$partdev" /mnt || rk3326_upgrade_abort 'cannot restore configuration'
	cp -f "$UPGRADE_BACKUP" "/mnt/$BACKUP_FILE" || failed=1
	if [ -d /tmp/handheld-boot ]; then cp -Rf /tmp/handheld-boot/. /mnt/ || failed=1; fi
	sync
	umount /mnt || failed=1
	[ "$failed" = 0 ] || rk3326_upgrade_abort 'configuration restore failed'
}

platform_do_upgrade() {
	local partdev part start size
	platform_check_image "$1" || rk3326_upgrade_abort 'image or partition validation failed'
	export_bootdevice || rk3326_upgrade_abort 'boot device unavailable'
	sync
	while read -r part start size; do
		export_partdevice partdev "$part" || rk3326_upgrade_abort "partition $part unavailable"
		echo "Writing image to /dev/$partdev..."
		(
			set -o pipefail
			rk3326_image_stream "$1" | {
				dd of="/dev/$partdev" ibs=512 obs=1M skip="$start" count="$size" iflag=fullblock conv=fsync || exit 1
				cat >/dev/null
			}
		) || rk3326_upgrade_abort "write failed on partition $part"
	done < /tmp/partmap.image
	# boot.scr discovers PARTUUID at boot. Preserve the existing disk signature,
	# bootloader and any additional games partition instead of changing them.
	sync
}
