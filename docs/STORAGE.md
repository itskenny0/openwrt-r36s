# EASYROMS storage

Flash the matching `*-sdcard.img.gz` for a new card. On its first boot, the console adds partition 3 to the **OS SD card**, starting at 640 MiB and using the remaining capacity. It performs a quick exFAT format, labels the volume `EASYROMS`, and mounts it read-write at `/easyroms`. EmulationStation creates the system, BIOS, save and state directories there. No second card or manual partitioning is required. The card needs at least 64 MiB beyond the system image; this MBR layout supports cards smaller than 2 TiB.

The bootloader, 64 MiB boot partition and 512 MiB root partition are left intact. The mounted root device identifies the OS card, so setup does not assume it is `mmcblk0` or partition an inserted USB drive/second card. Only the expected image layout is accepted. Existing third or fourth partitions with a different layout are left untouched; setup reports an error rather than overwriting them.

## Copying games

Use the [system folders](EMULATORS.md) under `/easyroms`. You can copy over SSH/SCP, or shut the console down fully and insert its SD card into a computer that supports exFAT. The volume is named `EASYROMS`. Safely eject it before returning it to the console. Never remove the running console's OS card.

BIOS files live under `/easyroms/bios`, saves under `/easyroms/saves/<system>` and save states under `/easyroms/states/<system>`. exFAT does not support Unix symlinks; bundled PSP and arcade support assets are copied to the games volume when needed.

A separate games card can be configured through **LuCI → System → Mount Points**. Disable the automatic `easyroms` mount before enabling the other card at `/easyroms`. An enabled custom mount is respected even when its card is absent; missing storage blocks game launches instead of writing substitute saves to the OS overlay.

## Interrupted setup and upgrades

Initialization records its disk identity, partition bounds and phase in `/etc/easyroms.state` before changing the partition table or formatting. Only an initial format recorded as incomplete may be repeated. A completed volume is never reformatted by normal boot. The service mounts only after recording completion, and later boots use the UUID in OpenWrt's regular UCI `fstab` configuration. No reboot is needed to register the new partition.

Configuration-preserving and reset sysupgrades write only the boot and root partitions. The EASYROMS partition and its files remain intact. After a reset upgrade, setup recognizes the existing exFAT third partition and recreates its mount configuration without formatting it. Keep backups of valuable saves: neither exFAT nor the SD card protects against every power failure or device fault.

When upgrading an older installation, configured `/roms` mounts are retargeted to `/easyroms`, and retained frontend paths are updated. If an old root-filesystem `/roms` directory is present and nonempty, setup exposes it at `/easyroms` and skips automatic partitioning so its contents are not hidden. Move/back up those files before requesting automatic setup. Root-filesystem games are not preserved by sysupgrade's configuration backup.

Reflashing a whole SD image is different from sysupgrade: it replaces the partition table. Back up games and saves before reflashing or repartitioning.

## Troubleshooting

```sh
logread -e handheld-storage
block info
mount | grep easyroms
uci show fstab
cat /etc/easyroms.state
```

A setup failure leaves the frontend's Tools menu available. Fix the reported condition and run `/etc/init.d/easyroms start`, or reboot. Do not delete the journal or run `mkfs.exfat` to repair a populated volume. Back up the card and check the unmounted filesystem with `fsck.exfat` or the computer's exFAT repair tool. Normal boots do not run a full filesystem scan, to keep startup fast.

Partition creation, exFAT formatting, recovery control flow and upgrade preservation are checked automatically on disposable disk images. Physical SD-card boot, host access and power-loss behavior still require hardware testing.
