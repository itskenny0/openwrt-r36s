// SPDX-License-Identifier: GPL-2.0
/*
 * Copyright (C) 2017 Rockchip Electronics Co. Ltd.
 *
 * Ported from the Rockchip vendor BSP kernel
 * (https://github.com/rockchip-linux/kernel, drivers/soc/rockchip/
 * rockchip-cpuinfo.c as of 84d26633c7a4) for PX30S/RK3326S support. The
 * only change from upstream is dropping the CONFIG_NO_GKI legacy ATAG
 * serial-number block, which depends on asm/system_info.h - an arm32-only
 * header that doesn't exist on arm64, and CONFIG_NO_GKI itself is an
 * Android-GKI-specific config not applicable here either way.
 */

#include <linux/crc32.h>
#include <linux/io.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/nvmem-consumer.h>
#include <linux/platform_device.h>
#include <linux/sizes.h>
#include <linux/slab.h>
#include <linux/rockchip/cpu.h>

unsigned long rockchip_soc_id;
EXPORT_SYMBOL(rockchip_soc_id);

static int rockchip_cpuinfo_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct nvmem_cell *cell;
	unsigned char *efuse_buf;
	size_t len = 0;
	u32 serial_low, serial_high;
	unsigned char buf[16];
	int i;

	cell = nvmem_cell_get(dev, "cpu-code");
	if (!IS_ERR(cell)) {
		efuse_buf = nvmem_cell_read(cell, &len);
		nvmem_cell_put(cell);
		if (IS_ERR(efuse_buf))
			return PTR_ERR(efuse_buf);

		if (len == 2)
			rockchip_set_cpu((efuse_buf[0] << 8 | efuse_buf[1]));
		kfree(efuse_buf);
	}

	cell = nvmem_cell_get(dev, "cpu-version");
	if (!IS_ERR(cell)) {
		efuse_buf = nvmem_cell_read(cell, &len);
		nvmem_cell_put(cell);
		if (IS_ERR(efuse_buf))
			return PTR_ERR(efuse_buf);

		if ((len == 1) && (efuse_buf[0] > rockchip_get_cpu_version()))
			rockchip_set_cpu_version(efuse_buf[0]);
		kfree(efuse_buf);
	}

	cell = nvmem_cell_get(dev, "id");
	if (IS_ERR(cell)) {
		dev_err(dev, "failed to get id cell: %ld\n", PTR_ERR(cell));
		return PTR_ERR(cell);
	}
	efuse_buf = nvmem_cell_read(cell, &len);
	nvmem_cell_put(cell);
	if (IS_ERR(efuse_buf))
		return PTR_ERR(efuse_buf);

	if (len != 16) {
		kfree(efuse_buf);
		dev_err(dev, "invalid id len: %zu\n", len);
		return -EINVAL;
	}

	for (i = 0; i < 8; i++) {
		buf[i] = efuse_buf[1 + (i << 1)];
		buf[i + 8] = efuse_buf[i << 1];
	}

	kfree(efuse_buf);

	dev_info(dev, "SoC\t\t: %lx\n", rockchip_soc_id);

	serial_low = crc32(0, buf, 8);
	serial_high = crc32(serial_low, buf + 8, 8);
	dev_info(dev, "Serial\t\t: %08x%08x\n", serial_high, serial_low);

	return 0;
}

static const struct of_device_id rockchip_cpuinfo_of_match[] = {
	{ .compatible = "rockchip,cpuinfo", },
	{ },
};
MODULE_DEVICE_TABLE(of, rockchip_cpuinfo_of_match);

static struct platform_driver rockchip_cpuinfo_driver = {
	.probe = rockchip_cpuinfo_probe,
	.driver = {
		.name = "rockchip-cpuinfo",
		.of_match_table = rockchip_cpuinfo_of_match,
	},
};

static void px30_init(void)
{
	void __iomem *base;

	rockchip_soc_id = ROCKCHIP_SOC_PX30;
#define PX30_DDR_GRF_BASE	0xFF630000
#define PX30_DDR_GRF_CON1	0x04
	base = ioremap(PX30_DDR_GRF_BASE, SZ_4K);
	if (base) {
		unsigned int val = readl_relaxed(base + PX30_DDR_GRF_CON1);

		if (((val >> 14) & 0x03) == 0x03)
			rockchip_soc_id = ROCKCHIP_SOC_PX30S;
		iounmap(base);
	}
}

static void rv1109_init(void)
{
	rockchip_soc_id = ROCKCHIP_SOC_RV1109;
}

static void rv1126_init(void)
{
	rockchip_soc_id = ROCKCHIP_SOC_RV1126;
}

static void rk3288_init(void)
{
	void __iomem *base;

	rockchip_soc_id = ROCKCHIP_SOC_RK3288;
#define RK3288_HDMI_PHYS	0xFF980000
	base = ioremap(RK3288_HDMI_PHYS, SZ_4K);
	if (base) {
		/* RK3288W HDMI Revision ID is 0x1A */
		if (readl_relaxed(base + 4) == 0x1A)
			rockchip_soc_id = ROCKCHIP_SOC_RK3288W;
		iounmap(base);
	}
}

static void rk3126_init(void)
{
	void __iomem *base;

	rockchip_soc_id = ROCKCHIP_SOC_RK3126;
#define RK312X_GRF_PHYS		0x20008000
#define RK312X_GRF_SOC_CON1	0x00000144
#define RK312X_GRF_CHIP_TAG	0x00000300
	base = ioremap(RK312X_GRF_PHYS, SZ_4K);
	if (base) {
		if (readl_relaxed(base + RK312X_GRF_CHIP_TAG) == 0x3136) {
			if (readl_relaxed(base + RK312X_GRF_SOC_CON1) & 0x1)
				rockchip_soc_id = ROCKCHIP_SOC_RK3126C;
			else
				rockchip_soc_id = ROCKCHIP_SOC_RK3126B;
		}
		iounmap(base);
	}
}

static void rk3308_init(void)
{
	void __iomem *base;

	rockchip_soc_id = ROCKCHIP_SOC_RK3308;
#define RK3308_GRF_PHYS		0xFF000000
#define RK3308_GRF_CHIP_ID	0x800
	base = ioremap(RK3308_GRF_PHYS, SZ_4K);
	if (base) {
		u32 v = readl_relaxed(base + RK3308_GRF_CHIP_ID);

		if (v == 0x3308)
			rockchip_soc_id = ROCKCHIP_SOC_RK3308B;
		if (v == 0x3308c)
			rockchip_soc_id = ROCKCHIP_SOC_RK3308BS;
		iounmap(base);
	}
}

#define RK356X_PMU_GRF_PHYS		0xfdc20000
#define RK356X_PMU_GRF_SOC_CON0		0x00000100
#define RK356X_CHIP_VERSION_MASK	0x00008000
static void rk356x_set_cpu_version(void)
{
	void __iomem *base;

	base = ioremap(RK356X_PMU_GRF_PHYS, SZ_4K);
	if (base) {
		if (readl_relaxed(base + RK356X_PMU_GRF_SOC_CON0) & RK356X_CHIP_VERSION_MASK)
			rockchip_set_cpu_version(1);
		iounmap(base);
	}
}

static void rk3566_init(void)
{
	rockchip_soc_id = ROCKCHIP_SOC_RK3566;
	rk356x_set_cpu_version();
}

static void rk3568_init(void)
{
	rockchip_soc_id = ROCKCHIP_SOC_RK3568;
	rk356x_set_cpu_version();
}

int __init rockchip_soc_id_init(void)
{
	if (rockchip_soc_id)
		return 0;

	if (cpu_is_rk3288()) {
		rk3288_init();
	} else if (cpu_is_rk312x()) {
		if (of_machine_is_compatible("rockchip,rk3128"))
			rockchip_soc_id = ROCKCHIP_SOC_RK3128;
		else
			rk3126_init();
	} else if (cpu_is_rk3308()) {
		rk3308_init();
	} else if (cpu_is_rv1109()) {
		rv1109_init();
	} else if (cpu_is_rv1126()) {
		rv1126_init();
	} else if (cpu_is_rk3566()) {
		rk3566_init();
	} else if (cpu_is_rk3568()) {
		rk3568_init();
	} else if (cpu_is_px30()) {
		px30_init();
	}

	return 0;
}
#ifndef MODULE
pure_initcall(rockchip_soc_id_init);
#endif

static int __init rockchip_cpuinfo_init(void)
{
#ifdef MODULE
	rockchip_soc_id_init();
#endif
	return platform_driver_register(&rockchip_cpuinfo_driver);
}
subsys_initcall_sync(rockchip_cpuinfo_init);

static void __exit rockchip_cpuinfo_exit(void)
{
	platform_driver_unregister(&rockchip_cpuinfo_driver);
}
module_exit(rockchip_cpuinfo_exit);

MODULE_LICENSE("GPL");
