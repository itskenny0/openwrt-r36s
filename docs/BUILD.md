# Building firmware

Use a Linux x86-64 build host. Ubuntu 24.04 is the CI reference. Allow at least 60 GiB of free storage for all profiles, and build as an ordinary user. All downloads, build products and temporary project files live inside the checkout.

```sh
sudo apt-get update
sudo apt-get install build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev python3 python3-setuptools python3-pyelftools python3-dev \
  rsync swig unzip zlib1g-dev file wget curl libelf-dev device-tree-compiler qemu-user proot busybox bsdextrautils iproute2 util-linux fdisk exfatprogs
git clone https://github.com/itskenny0/openwrt-r36s.git
cd openwrt-r36s
./scripts/rk3326-configure.sh all
make -j8 download
make -j"$(nproc)"
```

Use `./scripts/rk3326-configure.sh r36s` for just the original R36S Panel 4 image. The script resets `.config` to the tracked defaults. Run `make menuconfig` afterwards for local changes. Run only one build command at a time in a checkout; overlapping tools/toolchain builds can damage configure caches.

Images and manifests appear in `bin/targets/rk3326/generic/`; binary packages appear in `bin/packages/`. These are complete SD images with boot firmware, a FAT boot partition and a squashfs root with writable ext4 overlay. The boot command explicitly selects ext4 for the overlay and the image includes its formatting tools.

The 32 MiB region before the first partition reserves Rockchip bootloader slots: DDR/miniloader at sector 64, U-Boot at sector 16384, and BL31 trust at sector 24576. The boot partition starts at 32 MiB and is 64 MiB. The root partition is 512 MiB and ends at 640 MiB. First boot adds an exFAT third partition covering the remaining card capacity; the downloadable image retains only its two fixed OS partitions. Every profile includes all available DTBs; its boot script selects the appropriate default.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/rk3326-systems.py --check
python3 scripts/rk3326-check-config.py
python3 scripts/rk3326-check-firmware.py
python3 scripts/rk3326-check-kernel.py build_dir/target-*/linux-rk3326*/linux-6.18.*/.config
python3 scripts/rk3326-check-images.py bin/targets/rk3326/generic
python3 scripts/rk3326-smoke.py
python3 scripts/rk3326-storage-smoke.py
python3 scripts/rk3326-shutdown-smoke.py
python3 scripts/rk3326-upgrade-smoke.py
sudo python3 scripts/rk3326-network-smoke.py
python3 scripts/rk3326-ui-smoke.py
```

Storage integration tests use real `sfdisk`, `mkfs.exfat` and `fsck.exfat` on disposable files, with kernel device registration and mounts simulated. They check first-boot layout, preservation of every OS byte, repeated boots, interrupted setup, existing volumes and refusal of unsafe layouts.

The image check expects all profiles. It checks fwtool metadata, the gzip stream, partition bounds, bootloader slots, squashfs magic, the arm64 kernel, U-Boot script checksum and every DTB in the FAT filesystem. The kernel check inspects the resolved configuration and fails if a boot-critical driver became a module or was dropped. The firmware check reads the networking modules' compiled firmware filenames and requires the corresponding files and symlink targets in the final root filesystem.

The storage smoke check runs the packaged ARM64 shell, OpenWrt UCI/functions, partitioner and exFAT tools against an enlarged copy of the R36S image; device registration, probing and mounting remain simulated. It verifies provisioning, retained filesystems after normal/reset boots and configuration migration.

The QEMU smoke check loads every installed core, decodes original PNG/H.264 fixtures, checks PSP codecs, and renders an SDL/EGL/GLES framebuffer using Mesa softpipe. Original GB, NES, SNES, GBA, Mega Drive, PC Engine and PS1 programs exercise CPU execution, video, audio, cartridge RAM and save-state restoration. The UI test uses proot and SDL events to drive the actual EmulationStation menus, toggle USB Ethernet through a simulated helper boundary, launch a game with RetroArch, save and return, and show a missing-game error. The shutdown test stops the packaged session supervisor while RetroArch runs an original test cartridge, then checks save flushing and reloading across two launches. The target upgrade validator rejects gzip corruption even when fwtool metadata remains valid. A separate network namespace test connects a virtual USB host to the packaged DHCP server and checks the packaged SSH server greeting. The menu test also exercises persistent brightness and volume. Screenshots and logs are retained as CI artifacts. These tests do not emulate RK3326 display, input, audio or USB hardware, or establish game compatibility and speed.

## GitHub releases

`.github/workflows/rk3326.yml` runs integration checks and builds firmware on pushes to `main`, pull requests, manual dispatch and `v*` tags. A version tag publishes a **prerelease** only after a successful build, payload validation and a GitHub artifact attestation. Actions are pinned by commit. The release job alone has write permission.

```sh
git tag v0.1.0-rc1
git push origin v0.1.0-rc1
```

Assets include per-device images and manifests, `SHA256SUMS`, `build.config`, `feeds.lock`, `source.commit`, the hardware test checklist, emulator/networking/storage guides and `packages.tar.gz`. CI logs and temporary artifacts have limited retention; releases retain the published payload.

The package archive contains both `packages/` (userspace feeds) and `targets/rk3326/generic/packages/` (kernel modules), including signed indexes. Official snapshot feeds are disabled because this target and its kernel ABI are different. Extract the archive from the **same release** to a computer, serve that directory over HTTP, and put the desired `packages.adb` URLs in `/etc/apk/repositories.d/customfeeds.list`. Then use `apk update` and LuCI's package manager normally. The firmware already trusts the package signing key from its build; do not bypass signature checks. Packages absent from that archive require a new build with those packages selected.

Feeds are pinned in `feeds.conf.default`; custom package sources have explicit revisions and hashes. To reproduce a release, check out its tag and run the same configuration script. Update pins deliberately and run the complete checks again. Mesa and FFmpeg have private package names to avoid incompatible dependencies from unrelated feed packages.

## Upgrading a console

Upload the matching `sysupgrade.img.gz` through LuCI or use OpenWrt `sysupgrade`. Normal configuration-preserving upgrades save `boot.env`, custom overlays, UCI configuration and EmulationStation settings. A reset upgrade (`sysupgrade -n`) restores image defaults. The `/easyroms` partition and its games, saves and artwork are retained by sysupgrade, including reset upgrades. They are separate from the configuration backup. Files still stored in an older release's root-filesystem `/roms` directory are **not** retained; move or back them up before upgrading. See [storage](STORAGE.md).

Upgrade validation checks the entire compressed stream and exact partition sizes before any write. Changed layouts, missing partitions, failed panel backups and write errors stop the upgrade; the hooks cannot fall through to a success message. `sysupgrade -p` is intentionally rejected: changing the partition table requires writing a complete SD image.

When the partition layout matches, sysupgrade updates the boot and root partitions and leaves the installed bootloader, disk signature and any additional games partition in place. To change bootloader variants or refresh DDR/BL31 firmware, write a complete image to a spare SD card. Do not cross-flash profiles simply because they share an RK3326 processor.

## Verify release provenance

After downloading an image, verify both its checksum and its [GitHub build attestation](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations):

```sh
sha256sum --ignore-missing -c SHA256SUMS
gh attestation verify openwrt-rk3326-generic-gameconsole_r36s-squashfs-sysupgrade.img.gz \
  --repo itskenny0/openwrt-r36s \
  --signer-workflow itskenny0/openwrt-r36s/.github/workflows/rk3326.yml
```

Compare the verified source commit with the release tag and attached `source.commit`. The attestation identifies the CI workflow and payload digest; hardware validation remains a separate requirement.
