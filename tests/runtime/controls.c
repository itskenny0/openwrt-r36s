// SPDX-License-Identifier: GPL-2.0-only
#define HANDHELD_TEST
#include "../../package/system/rk3326-handheld/src/handheld-controls.c"
#include <assert.h>
static int poweroffs, steps, saves;
static int action(const char *command, const char *argument)
{
	(void)argument;
	if (!strcmp(command, "poweroff")) ++poweroffs;
	if (!strcmp(command, "volume-step")) ++steps;
	if (!strcmp(command, "volume-save")) ++saves;
	return 0;
}
static void send_event(int type, int code, int value, int64_t now)
{
	struct input_event ev = { .type = type, .code = code, .value = value };
	event(&inputs[0], &ev, now);
}
int main(void)
{
	for (int i = 0; i < MAX_INPUTS; ++i) inputs[i].fd = -1;
	inputs[0].fd = 10;
	// Initial held-key autorepeat and releases cannot shut the console down.
	send_event(EV_KEY, KEY_POWER, 2, 1000);
	tick(10000);
	assert(poweroffs == 0);
	send_event(EV_KEY, KEY_POWER, 1, 10000);
	send_event(EV_KEY, KEY_POWER, 0, 10500);
	tick(13000);
	assert(poweroffs == 0);
	// Lost events cancel pending power actions until another complete press.
	send_event(EV_KEY, KEY_POWER, 1, 14000);
	send_event(EV_SYN, SYN_DROPPED, 0, 14500);
	send_event(EV_KEY, KEY_POWER, 1, 15000);
	tick(18000);
	assert(poweroffs == 0);
	send_event(EV_SYN, SYN_REPORT, 0, 18000);
	// Debounce volume repeats; persist once after two idle seconds.
	send_event(EV_KEY, KEY_VOLUMEUP, 1, 19000);
	send_event(EV_KEY, KEY_VOLUMEUP, 2, 19010);
	send_event(EV_KEY, KEY_VOLUMEUP, 2, 19100);
	send_event(EV_KEY, KEY_VOLUMEUP, 0, 19200);
	assert(steps == 2);
	tick(21099);
	assert(saves == 0);
	tick(21100);
	tick(23000);
	assert(saves == 1);
	send_event(EV_SW, SW_HEADPHONE_INSERT, 1, 23000);
	assert(inputs[0].headphones);
	send_event(EV_SW, SW_HEADPHONE_INSERT, 0, 23001);
	assert(!inputs[0].headphones);
	// Repeats do not reset the power hold timer; shutdown fires just once.
	send_event(EV_KEY, KEY_POWER, 1, 24000);
	send_event(EV_KEY, KEY_POWER, 2, 25000);
	tick(25999);
	assert(poweroffs == 0);
	tick(26000);
	tick(28000);
	assert(poweroffs == 1);
	return 0;
}
