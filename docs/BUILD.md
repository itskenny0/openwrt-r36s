# Building firmware

Use a Linux x86-64 build host. Ubuntu 24.04 is the CI reference. Allow at least 60 GiB of free storage for all profiles, and build as an ordinary user. All downloads, build products and temporary project files live inside the checkout.

```sh
sudo apt-get update
sudo apt-get install build-essential clang flex bison g++ gawk gcc-multilib gettext git \
  libncurses-dev libssl-dev python3 python3-setuptools python3-pyelftools python3-dev \
  rsync swig unzip zlib1g-dev file wget curl libelf-dev device-tree-compiler qemu-user
git clone https://github.com/itskenny0/openwrt-r36s.git
cd openwrt-r36s
./scripts/rk3326-configure.sh all
make -j8 download
make -j"$(nproc)"
```

Use `./scripts/rk3326-configure.sh r36s` for just the original R36S Panel 4 image. The script resets `.config` to the tracked defaults. Run `make menuconfig` afterwards for local changes. Run only one build command at a time in a checkout; overlapping tools/toolchain builds can damage configure caches.

Images and manifests appear in `bin/targets/rk3326/generic/`; binary packages appear in `bin/packages/`. These are complete SD images with boot firmware, a FAT boot partition and a squashfs root with writable ext4 overlay. The boot command explicitly selects ext4 for the overlay and the image includes its formatting tools.

The 32 MiB region before the first partition reserves Rockchip bootloader slots: DDR/miniloader at sector 64, U-Boot at sector 16384, and BL31 trust at sector 24576. The boot partition starts at 32 MiB and is 64 MiB. The root partition is 512 MiB. Every profile includes all available DTBs; its boot script selects the appropriate default.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/rk3326-check-config.py
python3 scripts/rk3326-check-kernel.py build_dir/target-*/linux-rk3326*/linux-6.18.*/.config
python3 scripts/rk3326-check-images.py bin/targets/rk3326/generic
python3 scripts/rk3326-smoke.py
```

The image check expects all profiles. It checks fwtool metadata, the gzip stream, partition bounds, bootloader slots, squashfs magic, the arm64 kernel, U-Boot script checksum and every DTB in the FAT filesystem. The kernel check inspects the resolved configuration and fails if a boot-critical driver became a module or was dropped.

The QEMU smoke check runs the actual ARM64 libraries and programs: a generated PNG decode, ten Game Boy frames from a small self-authored test program, audio callbacks, and frontend version/help paths. It does not emulate RK3326 display, input, audio or USB hardware.

## GitHub releases

`.github/workflows/rk3326.yml` runs integration checks and builds firmware on pushes to `main`, pull requests, manual dispatch and `v*` tags. A version tag publishes a **prerelease** only after a successful build and payload validation. Actions are pinned by commit. The release job alone has write permission.

```sh
git tag v0.1.0-rc1
git push origin v0.1.0-rc1
```

Assets include per-device images and manifests, `SHA256SUMS`, `build.config`, `feeds.lock`, `source.commit`, the hardware test checklist and `packages.tar.gz`. CI logs and temporary artifacts have limited retention; releases retain the published payload.

The package archive contains both `packages/` (userspace feeds) and `targets/rk3326/generic/packages/` (kernel modules), including signed indexes. Official snapshot feeds are disabled because this target and its kernel ABI are different. Extract the archive from the **same release** to a computer, serve that directory over HTTP, and put the desired `packages.adb` URLs in `/etc/apk/repositories.d/customfeeds.list`. Then use `apk update` and LuCI's package manager normally. The firmware already trusts the package signing key from its build; do not bypass signature checks. Packages absent from that archive require a new build with those packages selected.

Feeds are pinned in `feeds.conf.default`; custom package sources have explicit revisions and hashes. To reproduce a release, check out its tag and run the same configuration script. Update pins deliberately and run the complete checks again. Mesa and FFmpeg have private package names to avoid incompatible dependencies from unrelated feed packages.

## Upgrading a console

Upload the matching `sysupgrade.img.gz` through LuCI or use OpenWrt `sysupgrade`. Normal configuration-preserving upgrades save `boot.env`, custom overlays, UCI configuration and EmulationStation settings. A reset upgrade (`sysupgrade -n`) restores image defaults. ROMs, saves and artwork on the root filesystem are **not** part of the configuration backup; keep them on a separate games card or back them up before upgrading.

When the partition layout matches, sysupgrade updates the boot and root partitions and leaves the installed bootloader in place. To change bootloader variants or refresh DDR/BL31 firmware, write a complete image to a spare SD card. Do not cross-flash profiles simply because they share an RK3326 processor.
