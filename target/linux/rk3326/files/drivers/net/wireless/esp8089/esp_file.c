/*
 * Copyright (c) 2010 -2014 Espressif System.
 *
 *   file operation in kernel space
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

#include <linux/fs.h>
#include <linux/vmalloc.h>
#include <linux/kernel.h>
#include <linux/version.h>
#include <linux/moduleparam.h>
#include <linux/firmware.h>
#include <linux/netdevice.h>
#include <linux/aio.h>
#include <linux/property.h>
#include <linux/of.h>
#include "esp_file.h"
#include "esp_debug.h"
#include "esp_sif.h"

static int mod_parm_crystal = -1;
module_param_named(crystal, mod_parm_crystal, int, 0444);
MODULE_PARM_DESC(crystal, "crystal frequency: 0=40MHz, 1=26MHz, 2=24MHz");

struct esp_init_table_elem esp_init_table[MAX_ATTR_NUM] = {
	/*
	 * Crystal type:
	 * 0: 40MHz (default)
	 * 1: 26MHz (ESP8266 ESP-12F)
	 * 2: 24MHz
	 */
	{"crystal_26M_en", 48, 0},
	/*
	 * Output crystal clock to pin:
	 * 0: None
	 * 1: GPIO1
	 * 2: URXD0
	 */
	{"test_xtal", 49, 0},
	/*
	 * Host SDIO mode:
	 * 0: Auto by pin strapping
	 * 1: SDIO data output on negative edges (SDIO v1.1)
	 * 2: SDIO data output on positive edges (SDIO v2.0)
	 */
	{"sdio_configure", 50, 2},
	/*
	 * WiFi/Bluetooth co-existence with BK3515A BT chip
	 * 0: None
	 * 1: GPIO0->WLAN_ACTIVE, MTMS->BT_ACTIVE, MTDI->BT_PRIORITY,
	 *    U0TXD->ANT_SEL_BT, U0RXD->ANT_SEL_WIFI
	 */
	{"bt_configure", 51, 0},
	/*
	 * Antenna selection:
	 * 0: Antenna is for WiFi
	 * 1: Antenna is for Bluetooth
	 */
	{"bt_protocol", 52, 0},
	/*
	 * Dual antenna configuration mode:
	 * 0: None
	 * 1: U0RXD + XPD_DCDC
	 * 2: U0RXD + GPIO0
	 * 3: U0RXD + U0TXD
	 */
	{"dual_ant_configure", 53, 0},
	/*
	 * Firmware debugging output pin:
	 * 0: None
	 * 1: UART TX on GPIO2
	 * 2: UART TX on U0TXD
	 */
	{"test_uart_configure", 54, 2},
	/*
	 * Whether to share crystal clock with BT (in sleep mode):
	 * 0: no
	 * 1: always on
	 * 2: automatically on according to XPD_DCDC
	 */
	{"share_xtal", 55, 0},
	/*
	 * Allow chip to be woken up during sleep on pin:
	 * 0: None
	 * 1: XPD_DCDC
	 * 2: GPIO0
	 * 3: Both XPD_DCDC and GPIO0
	 */
	{"gpio_wake", 56, 0},
	{"no_auto_sleep", 57, 0},
	{"speed_suspend", 58, 0},
	{"attr11", -1, -1},
	{"attr12", -1, -1},
	{"attr13", -1, -1},
	{"attr14", -1, -1},
	{"attr15", -1, -1},
	//attr that is not send to target
	/*
	 * Allow chip to be reset by GPIO pin:
	 * 0: no
	 * 1: yes
	 */
	{"ext_rst", -1, 0},
	{"wakeup_gpio", -1, 12},
	{"ate_test", -1, 0},
	{"attr19", -1, -1},
	{"attr20", -1, -1},
	{"attr21", -1, -1},
	{"attr22", -1, -1},
	{"attr23", -1, -1},
};

/*
 * Export part of the configuration related to first initiliazition to the esp8089
 */
void esp_conf_upload_first(void)
{
	int i;

	for (i = 0; i < MAX_ATTR_NUM; i++) {
		if (esp_init_table[i].value < 0)
			continue;

		if (!strcmp(esp_init_table[i].attr, "share_xtal"))
			sif_record_bt_config(esp_init_table[i].value);
		else if (!strcmp(esp_init_table[i].attr, "ext_rst"))
			sif_record_rst_config(esp_init_table[i].value);
		else if (!strcmp(esp_init_table[i].attr, "wakeup_gpio"))
			sif_record_wakeup_gpio_config(esp_init_table[i].value);
		else if (!strcmp(esp_init_table[i].attr, "ate_test"))
			sif_record_ate_config(esp_init_table[i].value);
	}
}

/*
 * Export part of the configuration related to second initiliazition
 */
void esp_conf_upload_second(u8 * init_data_buf, int buf_size)
{
	int i;

	for (i = 0; i < MAX_FIX_ATTR_NUM; i++) {
		if (esp_init_table[i].offset > -1
		    && esp_init_table[i].offset < buf_size
		    && esp_init_table[i].value > -1) {
			*(u8 *) (init_data_buf +
				 esp_init_table[i].offset) =
			    esp_init_table[i].value;
		} else if (esp_init_table[i].offset > buf_size) {
			esp_dbg(ESP_DBG_ERROR,
				"%s: offset[%d] longer than init_data_buf len[%d] Ignore\n",
				__FUNCTION__, esp_init_table[i].offset,
				buf_size);
		}
	}

}


void esp_conf_init(struct device *dev)
{

	struct device_node *np = dev->of_node;

	if (np) {

		u32 value;

		if (!of_property_read_u32(np, "esp,crystal-26M-en", &value))
			esp_conf_set_attr("crystal_26M_en", value);

		if (!of_property_read_u32(np, "esp,sdio-configure", &value))
			esp_conf_set_attr("sdio_configure", value);

		if (of_property_read_bool(np, "esp,shared-xtal"))
			esp_conf_set_attr("share_xtal", 1);

		if (!of_property_read_u32(np, "esp,gpio-wake", &value))
			esp_conf_set_attr("gpio_wake", value);

		if (!of_property_read_u32(np, "esp,wakeup-gpio", &value))
			esp_conf_set_attr("wakeup_gpio", value);

		if (of_property_read_bool(np, "esp,configure-dual-antenna"))
			esp_conf_set_attr("dual_ant_configure", 1);

		if (of_property_read_bool(np, "esp,no-auto-sleep"))
			esp_conf_set_attr("no_auto_sleep", 1);

		if (of_property_read_bool(np, "esp,test-xtal"))
			esp_conf_set_attr("test_xtal", 1);

		if (of_property_read_bool(np, "esp,bt-configure"))
			esp_conf_set_attr("bt_configure", 1);

		if (!of_property_read_u32(np, "esp,bt-protocol", &value))
			esp_conf_set_attr("bt_protocol", value);

		if (of_property_read_bool(np, "esp,test-uart-configure"))
			esp_conf_set_attr("test_uart_configure", 1);

		if (of_property_read_bool(np, "esp,speed-suspend"))
			esp_conf_set_attr("speed_suspend", 1);

		if (of_property_read_bool(np, "esp,ate-test"))
			esp_conf_set_attr("ate_test", 1);

		if (!of_property_read_u32(np, "esp,ext-rst", &value))
			esp_conf_set_attr("ext_rst", value);

	}

	if (mod_parm_crystal >= 0 && mod_parm_crystal <= 2)
		esp_conf_set_attr("crystal_26M_en", mod_parm_crystal);


	esp_conf_show_attrs();

}

int esp_conf_set_attr(char *name, u8 value) {

	int i;

	for (i = 0; i < MAX_ATTR_NUM; i++) {

		if (strcmp(esp_init_table[i].attr, name) == 0) {
			esp_dbg(ESP_DBG, "set config: %s value: %d", name, value);
			esp_init_table[i].value = value;
			return 0;
		}

	}

	return -1;

}

void esp_conf_show_attrs(void)
{
	int i;
	for (i = 0; i < MAX_ATTR_NUM; i++)
		if (esp_init_table[i].offset > -1)
			esp_dbg(ESP_SHOW, "config parm:%s (id:%d), value: %d\n",
				esp_init_table[i].attr,
				esp_init_table[i].offset,
				esp_init_table[i].value);
}
