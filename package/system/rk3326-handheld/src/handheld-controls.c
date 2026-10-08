// SPDX-License-Identifier: GPL-2.0-only
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <limits.h>
#include <linux/input.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <syslog.h>
#include <time.h>
#include <unistd.h>

#define MAX_INPUTS 32
#define BITS_PER_LONG (sizeof(unsigned long) * CHAR_BIT)
#define BIT_WORDS(n) (((n) + BITS_PER_LONG - 1) / BITS_PER_LONG)
#define POWER_HOLD_MS 2000

struct input {
	int fd;
	char path[PATH_MAX];
	bool dropped, power_down, headphones, has_jack;
	int64_t power_since;
};
static struct input inputs[MAX_INPUTS];
static bool shutting_down;
static int64_t volume_dirty, last_volume;
static volatile sig_atomic_t stopping;

static int64_t now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (int64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

static bool bit(const unsigned long *bits, unsigned int code)
{
	return !!(bits[code / BITS_PER_LONG] & (1UL << (code % BITS_PER_LONG)));
}

#ifndef HANDHELD_TEST
static int action(const char *command, const char *argument)
{
	pid_t pid = fork();
	if (pid < 0) return -1;
	if (!pid) {
		setpgid(0, 0);
		if (!strcmp(command, "poweroff")) execl("/sbin/poweroff", "poweroff", (char *)NULL);
		else execl("/usr/sbin/handheld-settings", "handheld-settings", command, argument, (char *)NULL);
		_exit(127);
	}
	setpgid(pid, pid);
	int status;
	int64_t deadline = now_ms() + 5000;
	for (;;) {
		pid_t result = waitpid(pid, &status, WNOHANG);
		if (result == pid) return WIFEXITED(status) && WEXITSTATUS(status) == 0 ? 0 : -1;
		if (result < 0 && errno != EINTR) return -1;
		if (now_ms() >= deadline) {
			kill(-pid, SIGKILL);
			while (waitpid(pid, &status, 0) < 0 && errno == EINTR) {}
			syslog(LOG_ERR, "Timed out applying %s", command);
			return -1;
		}
		usleep(10000);
	}
}
#else
static int action(const char *, const char *);
#endif

static void resync(struct input *input)
{
	unsigned long state[BIT_WORDS(SW_CNT)] = {0};
	// A held power key on startup or after a lost event must be released and
	// pressed again. Never interpret missing events as a shutdown request.
	input->power_down = false;
	input->power_since = 0;
	if (input->has_jack && ioctl(input->fd, EVIOCGSW(sizeof(state)), state) >= 0)
		input->headphones = bit(state, SW_HEADPHONE_INSERT);
}

static void event(struct input *input, const struct input_event *ev, int64_t now)
{
	if (ev->type == EV_SYN && ev->code == SYN_DROPPED) {
		input->dropped = true;
		input->power_down = false;
		return;
	}
	if (input->dropped) {
		if (ev->type == EV_SYN && ev->code == SYN_REPORT) {
			input->dropped = false;
			resync(input);
		}
		return;
	}
	if (ev->type == EV_SW && ev->code == SW_HEADPHONE_INSERT) input->headphones = ev->value != 0;
	if (ev->type != EV_KEY || shutting_down) return;
	if (ev->code == KEY_POWER) {
		if (ev->value == 1 && !input->power_down) {
			input->power_down = true;
			input->power_since = now;
		} else if (ev->value == 0) input->power_down = false;
	} else if ((ev->code == KEY_VOLUMEUP || ev->code == KEY_VOLUMEDOWN) &&
	           (ev->value == 1 || ev->value == 2) && now - last_volume >= 100) {
		if (!action("volume-step", ev->code == KEY_VOLUMEUP ? "up" : "down")) volume_dirty = now;
		last_volume = now;
	}
}

static void tick(int64_t now)
{
	if (volume_dirty && now - volume_dirty >= 2000) {
		if (action("volume-save", NULL)) syslog(LOG_ERR, "Cannot save volume");
		volume_dirty = 0;
	}
	for (int i = 0; i < MAX_INPUTS && !shutting_down; ++i) {
		if (inputs[i].fd >= 0 && inputs[i].power_down && now - inputs[i].power_since >= POWER_HOLD_MS) {
			if (volume_dirty) { action("volume-save", NULL); volume_dirty = 0; }
			shutting_down = action("poweroff", NULL) == 0;
			inputs[i].power_down = false;
		}
	}
}

#ifndef HANDHELD_TEST
static void scan(void)
{
	glob_t paths;
	if (glob("/dev/input/event*", 0, NULL, &paths)) { globfree(&paths); return; }
	for (size_t p = 0; p < paths.gl_pathc; ++p) {
		int slot = -1;
		bool found = false;
		for (int i = 0; i < MAX_INPUTS; ++i) {
			if (inputs[i].fd < 0) slot = i;
			else if (!strcmp(inputs[i].path, paths.gl_pathv[p])) found = true;
		}
		if (found || slot < 0) continue;
		int fd = open(paths.gl_pathv[p], O_RDONLY | O_NONBLOCK | O_CLOEXEC);
		if (fd < 0) continue;
		unsigned long keys[BIT_WORDS(KEY_CNT)] = {0}, switches[BIT_WORDS(SW_CNT)] = {0};
		ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(keys)), keys);
		ioctl(fd, EVIOCGBIT(EV_SW, sizeof(switches)), switches);
		bool jack = bit(switches, SW_HEADPHONE_INSERT);
		if (!jack && !bit(keys, KEY_POWER) && !bit(keys, KEY_VOLUMEUP) && !bit(keys, KEY_VOLUMEDOWN)) {
			close(fd);
			continue;
		}
		struct input *input = &inputs[slot];
		memset(input, 0, sizeof(*input));
		input->fd = fd;
		input->has_jack = jack;
		snprintf(input->path, sizeof(input->path), "%s", paths.gl_pathv[p]);
		resync(input);
	}
	globfree(&paths);
}

static void stop(int sig) { (void)sig; stopping = 1; }

int main(void)
{
	openlog("handheld-controls", LOG_PID, LOG_DAEMON);
	signal(SIGTERM, stop);
	signal(SIGINT, stop);
	for (int i = 0; i < MAX_INPUTS; ++i) inputs[i].fd = -1;
	int64_t next_scan = 0;
	int routed = -1;
	bool restored = false;
	while (!stopping) {
		int64_t now = now_ms();
		if (now >= next_scan) {
			scan();
			if (!restored) restored = action("restore", NULL) == 0;
			next_scan = now_ms() + 2000;
		}
		struct pollfd fds[MAX_INPUTS];
		for (int i = 0; i < MAX_INPUTS; ++i) fds[i] = (struct pollfd){inputs[i].fd, POLLIN, 0};
		if (poll(fds, MAX_INPUTS, 100) < 0 && errno != EINTR) break;
		for (int i = 0; i < MAX_INPUTS; ++i) {
			if (!fds[i].revents) continue;
			struct input_event ev;
			ssize_t count;
			while ((count = read(inputs[i].fd, &ev, sizeof(ev))) == sizeof(ev)) event(&inputs[i], &ev, now_ms());
			if (count == 0 || (count < 0 && errno != EAGAIN && errno != EINTR) ||
			    (fds[i].revents & (POLLHUP | POLLERR | POLLNVAL))) {
				close(inputs[i].fd);
				inputs[i].fd = -1;
				inputs[i].power_down = inputs[i].headphones = false;
			}
		}
		bool headphones = false;
		for (int i = 0; i < MAX_INPUTS; ++i) if (inputs[i].fd >= 0 && inputs[i].headphones) headphones = true;
		if (restored && routed != headphones && !action("route", headphones ? "headphones" : "speaker")) routed = headphones;
		tick(now_ms());
	}
	if (volume_dirty) action("volume-save", NULL);
	for (int i = 0; i < MAX_INPUTS; ++i) if (inputs[i].fd >= 0) close(inputs[i].fd);
	closelog();
	return 0;
}
#endif
