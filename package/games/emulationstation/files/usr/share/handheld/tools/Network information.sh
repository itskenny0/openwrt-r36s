#!/bin/sh
clear
printf 'OpenWrt handheld\n\n'
printf 'USB Ethernet: '
if handheld-usb status; then echo enabled; else echo disabled; fi
printf 'LuCI: http://%s/\n' "$(handheld-usb address)"
printf '\nUse START > NETWORK SETTINGS to change USB mode.\n'
printf '\nReturning to EmulationStation in 8 seconds.\n'
sleep 8
