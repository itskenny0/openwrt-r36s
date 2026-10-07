# Hardware validation and boot timing

Hardware results are pending. Cross-compilation, shell integration tests and image inspection do not validate electrical behavior, display timing, controller mapping or USB enumeration on a console. Releases remain prereleases until those checks have been performed.

Record the release tag, image checksum, exact board/panel revision, SD card model and host OS with every result. Keep the working stock card intact.

## First boot checklist

1. Cold boot on battery. Confirm the selected panel initializes without flickering, artifacts or incorrect rotation. Repeat with charging connected.
2. Confirm EmulationStation appears and every button, D-pad direction and stick works. Check menu accept/back and Start. Confirm the correct mapping is used after reboot.
3. Launch a legally obtained Game Boy test ROM, check audio/video and exit with Select + Start. Check saves persist after shutdown and reboot.
4. Enable USB Ethernet in Start → Network Settings. On Linux, macOS and Windows, confirm enumeration, DHCP, ping, SSH and LuCI. Set a root password. Repeat cable unplug/replug and reboot with the setting enabled.
5. Disable USB Ethernet and attach a supported USB Wi-Fi or Ethernet adapter. Verify link, DHCP and traffic, then switch back. Test Bluetooth discovery/pairing with a supported adapter. Record chipset IDs and firmware errors from the kernel log.
6. Check battery/charging information, speaker and headphone output, brightness and temperatures during an extended game session. Headphone routing may require ALSA mixer adjustment in this initial port.
7. Shut down from EmulationStation and verify the PMIC turns the device off. Do not use a hard power cut as a routine shutdown.
8. Perform a configuration-preserving sysupgrade on a spare card. Confirm the panel override, USB mode, LuCI password and controller configuration survive. Test a reset upgrade separately.

Useful evidence over SSH:

```sh
ubus call system board
uname -a
cat /proc/cmdline
dmesg
logread
cat /sys/class/drm/card*-*/status
cat /sys/class/usb_role/*/role
ls /sys/class/udc
ubus call network.interface.lan status
aplay -l
amixer scontents
```

For a blank screen, inspect `boot.env` and the selected DTB on a computer first. For serial diagnosis, use the board's actual UART pinout and voltage. The default console is `ttyS2` at 1500000 baud; clone DT aliases can map that name to UART5. The login prompt stays on serial so it does not compete with EmulationStation on the display's virtual terminal.

## Boot optimization

The production configuration uses a zero-second U-Boot countdown, a raw arm64 kernel, no initramfs, no preinit wait, quiet console output, and built-in SD/MMC, regulators, display, Panfrost, input, audio and USB gadget support. The squashfs root uses Zstandard at level 3 to favor fast decompression. EmulationStation runs directly on KMS/DRM and waits for a connected display instead of sleeping for a fixed delay. It does not wait for DHCP, Wi-Fi, Bluetooth or an internet connection. Kernel debug information and verbose diagnostic facilities are disabled in the release configuration.

Networking drivers are retained. No `lpj` shortcut, `rootwait` removal, blind asynchronous probing or aggressive frequency/voltage override is used: those can trade boot time for intermittent failures.

There is **no measured boot-time claim yet**. Measure power-button press to the first interactive EmulationStation frame with video over at least ten cold boots. Report median and slowest time. Test USB host and saved gadget mode, with/without adapters, on the same SD card. Check the menu responds; a displayed splash alone is not a completed boot.

For diagnosis, temporarily remove `quiet loglevel=3` and append `printk.time=1 initcall_debug` to `bootargs` in a rebuilt `boot.scr`. Collect a serial trace and `/proc/uptime` when the frontend becomes interactive. Do not use those verbose builds as the performance baseline. Separate boot-ROM/DDR/U-Boot time, kernel time, root mount/overlay time and frontend startup before changing the next bottleneck.
