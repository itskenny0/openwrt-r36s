// SPDX-License-Identifier: GPL-2.0-only
#include <libretro.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned frames;
static size_t samples;
static bool environment(unsigned cmd, void *data) {
    if (cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT) return true;
    if (cmd == RETRO_ENVIRONMENT_GET_CAN_DUPE) { *(bool *)data = true; return true; }
    if (cmd == RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE) { *(bool *)data = false; return true; }
    if (cmd == RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY || cmd == RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY) {
        *(const char **)data = getenv("HOME"); return true;
    }
    return false;
}
static void video(const void *data, unsigned w, unsigned h, size_t pitch) {
    if (data && w == 160 && h == 144 && pitch >= w * 2) ++frames;
}
static void audio(int16_t left, int16_t right) { ++samples; }
static size_t batch(const int16_t *data, size_t count) { samples += count; return count; }
static void poll(void) {}
static int16_t input(unsigned port, unsigned device, unsigned index, unsigned id) { return 0; }
int main(void) {
    static uint8_t rom[32768];
    memcpy(rom + 0x134, "OPENWRT TEST", 12);
    rom[0x100] = 0x18; rom[0x101] = 0xfe; /* Self-authored JR loop. */
    uint8_t sum = 0;
    for (unsigned i = 0x134; i <= 0x14c; ++i) sum = sum - rom[i] - 1;
    rom[0x14d] = sum;
    retro_set_environment(environment); retro_set_video_refresh(video);
    retro_set_audio_sample(audio); retro_set_audio_sample_batch(batch);
    retro_set_input_poll(poll); retro_set_input_state(input);
    retro_init();
    struct retro_game_info game = { .data = rom, .size = sizeof rom };
    if (!retro_load_game(&game)) return 1;
    for (unsigned i = 0; i < 10; ++i) retro_run();
    retro_unload_game(); retro_deinit();
    printf("Gambatte: %u frames, %zu audio samples on aarch64/musl.\n", frames, samples);
    return frames >= 8 && samples > 0 ? 0 : 2;
}
