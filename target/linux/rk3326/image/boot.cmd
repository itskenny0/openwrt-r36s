# The bootloader supplies devtype/devnum. boot.env can select another DTB/panel.
setenv fdtfile @DTB@.dtb
setenv overlay
setenv env_addr_r 0x00600000
setenv kernel_addr_r 0x02080000
setenv fdt_addr_r 0x08300000
setenv fdtoverlay_addr_r 0x08700000
if load ${devtype} ${devnum}:1 ${env_addr_r} boot.env; then
  env import -t ${env_addr_r} ${filesize}
fi
part uuid ${devtype} ${devnum}:2 rootuuid
setenv bootargs "root=PARTUUID=${rootuuid} rootwait rw fstools_overlay_fstype=ext4 quiet loglevel=3 console=ttyS2,1500000 cma=64M"
if load ${devtype} ${devnum}:1 ${kernel_addr_r} Image; then
  if load ${devtype} ${devnum}:1 ${fdt_addr_r} dtbs/${fdtfile}; then
    fdt addr ${fdt_addr_r}
    fdt resize 65536
    if test -n "${overlay}"; then
      if load ${devtype} ${devnum}:1 ${fdtoverlay_addr_r} overlays/${overlay}; then
        if fdt apply ${fdtoverlay_addr_r}; then
          booti ${kernel_addr_r} - ${fdt_addr_r}
        else
          echo "Panel overlay failed; refusing to boot an invalid device tree"
        fi
      else
        echo "Panel overlay missing"
      fi
    else
      booti ${kernel_addr_r} - ${fdt_addr_r}
    fi
  fi
fi
