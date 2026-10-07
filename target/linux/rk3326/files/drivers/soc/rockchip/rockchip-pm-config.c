// SPDX-License-Identifier: GPL-2.0
/*
 * Rockchip PX30S suspend-to-RAM wakeup configuration.
 *
 * Not ported from upstream - trimmed from the vendor BSP kernel
 * (https://github.com/rockchip-linux/kernel, drivers/soc/rockchip/
 * rockchip_pm_config.c), which mainline lacks entirely. Forwards this
 * board's rockchip,sleep-mode-config and rockchip,wakeup-config values to
 * BL31 firmware via the SIP_SUSPEND_MODE SMC call - on PX30S the deepest
 * suspend states are governed by firmware, not Linux, so these values
 * have to reach BL31 for it to know what to arm as a wake source.
 *
 * A previous attempt at this only sent mode/wakeup config once, at probe
 * time. The vendor driver additionally sends LINUX_PM_STATE - which
 * suspend state (mem/standby/freeze) is actually being entered - from a
 * dev_pm_ops .prepare hook that runs on every single suspend attempt, and
 * re-sends mode/wakeup config at the same time. That's the piece this
 * adds: without ever telling firmware which state Linux is entering, BL31
 * may not arm the deep power-down/wake path the same way it would if
 * this call were present, regardless of whether the mode/wakeup config
 * values themselves are correct.
 *
 * Trimmed relative to the vendor source: this board's own rockchip-
 * suspend node only ever sets rockchip,sleep-debug-en/sleep-mode-config/
 * wakeup-config, so the regulator on/off lists, virtual-poweroff,
 * mcu-sleep-cfg, PM-domain linking, and multi-state (mem-lite/mem-ultra)
 * handling are all dropped entirely rather than ported unused.
 *
 * NOT yet confirmed fixing wake-from-sleep on real hardware.
 */

#include <linux/arm-smccc.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/suspend.h>

#define SIP_SUSPEND_MODE		0x82000003

#define SUSPEND_MODE_CONFIG		0x01
#define WKUP_SOURCE_CONFIG		0x02
#define SUSPEND_DEBUG_ENABLE		0x05
#define LINUX_PM_STATE			0x09

static u32 rk_pm_sleep_mode_config;
static u32 rk_pm_wakeup_config;

static int rockchip_pm_sip_config(u32 ctrl, u32 config1, u32 config2)
{
	struct arm_smccc_res res;

	arm_smccc_smc(SIP_SUSPEND_MODE, ctrl, config1, config2, 0, 0, 0, 0,
		     &res);
	return res.a0;
}

/*
 * Runs on every suspend attempt (not just once at boot) - this is the
 * call an earlier attempt at this fix was missing entirely.
 */
static int rockchip_pm_config_prepare(struct device *dev)
{
	rockchip_pm_sip_config(LINUX_PM_STATE, mem_sleep_current, 0);

	if (rk_pm_sleep_mode_config)
		rockchip_pm_sip_config(SUSPEND_MODE_CONFIG,
					rk_pm_sleep_mode_config, 0);
	if (rk_pm_wakeup_config)
		rockchip_pm_sip_config(WKUP_SOURCE_CONFIG,
					rk_pm_wakeup_config, 0);

	return 0;
}

static const struct dev_pm_ops rockchip_pm_config_ops = {
	.prepare = rockchip_pm_config_prepare,
};

static int rockchip_pm_config_probe(struct platform_device *pdev)
{
	struct device_node *node = pdev->dev.of_node;
	u32 sleep_debug_en = 0;

	of_property_read_u32(node, "rockchip,sleep-mode-config",
			     &rk_pm_sleep_mode_config);
	of_property_read_u32(node, "rockchip,wakeup-config",
			     &rk_pm_wakeup_config);

	if (rk_pm_sleep_mode_config)
		rockchip_pm_sip_config(SUSPEND_MODE_CONFIG,
					rk_pm_sleep_mode_config, 0);
	if (rk_pm_wakeup_config)
		rockchip_pm_sip_config(WKUP_SOURCE_CONFIG,
					rk_pm_wakeup_config, 0);

	if (!of_property_read_u32(node, "rockchip,sleep-debug-en",
				  &sleep_debug_en))
		rockchip_pm_sip_config(SUSPEND_DEBUG_ENABLE, sleep_debug_en, 0);

	return 0;
}

static const struct of_device_id rockchip_pm_config_of_match[] = {
	{ .compatible = "rockchip,pm-px30", },
	{ },
};
MODULE_DEVICE_TABLE(of, rockchip_pm_config_of_match);

static struct platform_driver rockchip_pm_config_driver = {
	.probe = rockchip_pm_config_probe,
	.driver = {
		.name = "rockchip-pm-config",
		.of_match_table = rockchip_pm_config_of_match,
		.pm = &rockchip_pm_config_ops,
	},
};
module_platform_driver(rockchip_pm_config_driver);

MODULE_DESCRIPTION("Rockchip PX30S suspend mode config");
MODULE_LICENSE("GPL");
