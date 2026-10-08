# USB access and Wi-Fi clients

## USB Ethernet, SSH and LuCI

In EmulationStation, use **Start → Network Settings → USB Ethernet**, enable the switch and close the menu. Connect the OTG port to a computer with a data cable. The console is the USB device and DHCP server; the computer is the Ethernet/DHCP client.

On a fresh image:

| Setting | Value |
| --- | --- |
| Console / LuCI | `http://192.168.77.1/` |
| SSH | `ssh root@192.168.77.1` |
| Computer's DHCP pool | `192.168.77.100–192.168.77.249` |
| Netmask | `255.255.255.0` |
| USB functions | CDC ECM and RNDIS |

Enabling USB Ethernet enables the Dropbear, dnsmasq and uhttpd services and the default SSH instance. Existing passwords, SSH authentication choices, LAN address and DHCP lease range are retained. Set a root password in LuCI on first use. If you have customized SSH listen interfaces or firewall policy, include LAN in those rules. The helper rejects a LAN configured as a DHCP client or a missing DHCP pool.

Configuration-preserving upgrades retain their existing LAN address, including `192.168.1.1` from earlier beta images. **Connect to LuCI** in Network Settings shows the configured address. Use a LAN subnet different from the Wi-Fi network you want to join; fresh images choose `192.168.77.0/24` to avoid common home-router subnets.

The mode is saved only after configuration succeeds. A failed USB transition or failed setting write attempts to restore the previous role. Disabling the setting restores host mode for dongles and other USB peripherals. Physical ECM/RNDIS enumeration still needs testing on Linux, macOS and Windows.

## USB Wi-Fi client

The image includes mainline USB Wi-Fi drivers and firmware for rtl8xxxu, rtw88 8821CU/8723DU, MediaTek MT7601U and MT76x0U/MT76x2U families, plus supported built-in SDIO radios. See `HARDWARE.md` for the driver inventory. Match the dongle's USB chipset ID to a supported driver; a retail product name alone does not establish its chipset.

The OTG port cannot act as a USB Ethernet device and host a Wi-Fi dongle at the same time. On a console with one host-capable port, configure Wi-Fi before swapping the cable:

1. Enable USB Ethernet, connect the computer and SSH to the console.
2. Run `handheld-wifi configure`. Enter the network name and WPA2 passphrase at its prompts. The password is not echoed or passed on the helper's command line. The helper saves the configuration even if the dongle is not present yet.
3. On the console, turn USB Ethernet off in EmulationStation. Disconnect the cable and insert the Wi-Fi dongle. The radio hotplug hook enables the configured client when the driver registers it.
4. The `wwan` interface obtains an address from the access point. Check internet access using the frontend scraper, or reconnect USB Ethernet and inspect `logread` for association/DHCP failures. Wi-Fi and USB management can operate together when they use independent physical controllers, including built-in Wi-Fi.

The helper configures WPA2-Personal on `radio0` by default. For multiple radios, WPA3, enterprise authentication, static addressing or a different adapter selection, use regular OpenWrt wireless/UCI configuration or **LuCI → Network → Wireless**. In LuCI, scan, join the access point, assign the client to `wwan` with DHCP, and put it in the WAN firewall zone. Do not bridge a normal Wi-Fi station into `br-lan`.

The Wi-Fi client is an upstream WAN connection. It does not run a DHCP server on the access point's network or expose the console's management services through the default WAN firewall. Wi-Fi credentials and interface configuration survive a configuration-preserving sysupgrade.

## Diagnose a connection

Over SSH:

```sh
handheld-usb address
ubus call network.interface.lan status
ubus call network.interface.wwan status
wifi status
logread -e dnsmasq
logread -e wpa_supplicant
logread -e dropbear
dmesg
```

Check for missing firmware, a charging-only cable, a dongle still connected while the port is in gadget mode, or overlapping LAN/Wi-Fi subnets. Changing the USB role disconnects active sessions using that port.
