#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# RK3326 miniloader layout used by ROCKNIX. Output starts at SD sector 64.
set -eu
build=$(realpath "$1")
firmware=$(realpath "$2")
ddr=${3:-rk3326_ddr_333MHz_v2.11.bin}
cd "$build"
mkimage -n px30 -T rksd -d "$firmware/$ddr" idbloader.img
cat "$firmware/rk3326_miniloader_v1.40.bin" >> idbloader.img
"$firmware/loaderimage" --pack --uboot u-boot-dtb.bin uboot.img 0x00200000
cat > trust.ini <<EOF
[BL30_OPTION]
SEC=0
[BL31_OPTION]
SEC=1
PATH=$firmware/rk3326_bl31_v1.34.elf
ADDR=0x00010000
[BL32_OPTION]
SEC=0
[BL33_OPTION]
SEC=0
[OUTPUT]
PATH=trust.img
EOF
"$firmware/trust_merger" trust.ini
rm -f uboot.bin
dd if=idbloader.img of=uboot.bin bs=512 conv=notrunc status=none
dd if=uboot.img of=uboot.bin bs=512 seek=16320 conv=notrunc status=none
dd if=trust.img of=uboot.bin bs=512 seek=24512 conv=notrunc status=none
test "$(stat -c %s uboot.bin)" -lt 33521664
