// SPDX-License-Identifier: GPL-2.0-only
// Execute real target cores with original test programs, then round-trip states.
#include <libretro.h>
#include <dlfcn.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned frames, coloured, format = RETRO_PIXEL_FORMAT_0RGB1555;
static size_t samples;
static struct { char *key, *value; } options[512];
static unsigned option_count;

static void log_message(enum retro_log_level level, const char *message, ...) {
    (void)level;
    va_list args;
    va_start(args, message);
    vfprintf(stderr, message, args);
    va_end(args);
}

static void option(const char *key, const char *value) {
    if (!key || !value || option_count == 512) return;
    options[option_count].key = strdup(key);
    options[option_count++].value = strdup(value);
}

static bool environment(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        format = *(unsigned *)data;
        return format <= RETRO_PIXEL_FORMAT_RGB565;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:
        *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
    case RETRO_ENVIRONMENT_GET_FASTFORWARDING:
        *(bool *)data = false; return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_CORE_ASSETS_DIRECTORY:
        *(const char **)data = getenv("HOME"); return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        ((struct retro_log_callback *)data)->log = log_message; return true;
    case RETRO_ENVIRONMENT_GET_LANGUAGE:
        *(unsigned *)data = RETRO_LANGUAGE_ENGLISH; return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        *(unsigned *)data = 2; return true;
    case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:
        return true;
    case RETRO_ENVIRONMENT_GET_INPUT_MAX_USERS:
        *(unsigned *)data = 1; return true;
    case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE:
        *(int *)data = 3; return true;
    case RETRO_ENVIRONMENT_SET_VARIABLES:
        for (const struct retro_variable *v = data; v && v->key; ++v) {
            const char *start = strstr(v->value, "; ");
            if (!start) continue;
            char *value = strdup(start + 2);
            char *end = strchr(value, '|');
            if (end) *end = 0;
            option(v->key, value);
            free(value);
        }
        return true;
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL: {
        const struct retro_core_option_definition *v1 = NULL;
        const struct retro_core_option_v2_definition *v2 = NULL;
        if (cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS) v1 = data;
        if (cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL)
            v1 = ((struct retro_core_options_intl *)data)->us;
        if (cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2)
            v2 = ((struct retro_core_options_v2 *)data)->definitions;
        if (cmd == RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL)
            v2 = ((struct retro_core_options_v2_intl *)data)->us->definitions;
        for (; v1 && v1->key; ++v1)
            option(v1->key, v1->default_value ? v1->default_value : v1->values[0].value);
        for (; v2 && v2->key; ++v2)
            option(v2->key, v2->default_value ? v2->default_value : v2->values[0].value);
        return true;
    }
    case RETRO_ENVIRONMENT_GET_VARIABLE: {
        struct retro_variable *variable = data;
        for (unsigned i = option_count; i; --i)
            if (!strcmp(variable->key, options[i - 1].key)) {
                variable->value = options[i - 1].value;
                return true;
            }
        variable->value = NULL;
        return false;
    }
    default:
        return false;
    }
}

static void video(const void *data, unsigned width, unsigned height, size_t pitch) {
    if (!data) return; // Duplicate frame; do not count it as newly rendered output.
    if (data == RETRO_HW_FRAME_BUFFER_VALID || !width || !height || width > 2048 || height > 2048)
        exit(10);
    unsigned bytes = format == RETRO_PIXEL_FORMAT_XRGB8888 ? 4 : 2;
    if (pitch < width * bytes) exit(11);
    ++frames;
    // Ignore unused high/alpha bits: a black framebuffer must not pass as colour.
    for (unsigned y = 0; y < height; ++y) {
        const uint8_t *line = (const uint8_t *)data + y * pitch;
        for (unsigned x = 0; x < width; ++x) {
            uint32_t pixel = 0;
            memcpy(&pixel, line + x * bytes, bytes);
            uint32_t mask = bytes == 4 ? 0xffffff : format == RETRO_PIXEL_FORMAT_RGB565 ? 0xffff : 0x7fff;
            if (pixel & mask) { ++coloured; return; }
        }
    }
}

static void audio(int16_t left, int16_t right) { (void)left; (void)right; ++samples; }
static size_t batch(const int16_t *data, size_t count) { (void)data; samples += count; return count; }
static void poll(void) {}
static int16_t input(unsigned port, unsigned device, unsigned index, unsigned id) {
    (void)port; (void)device; (void)index; (void)id; return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "%s\n", dlerror()); return 3; }
#define LOAD(name) __typeof__(name) *p_##name = dlsym(handle, #name); \
    if (!p_##name) { fprintf(stderr, "Missing %s\n", #name); return 4; }
    LOAD(retro_set_environment); LOAD(retro_set_video_refresh);
    LOAD(retro_set_audio_sample); LOAD(retro_set_audio_sample_batch);
    LOAD(retro_set_input_poll); LOAD(retro_set_input_state);
    LOAD(retro_init); LOAD(retro_deinit); LOAD(retro_get_system_info);
    LOAD(retro_load_game); LOAD(retro_unload_game); LOAD(retro_run);
    LOAD(retro_serialize_size); LOAD(retro_serialize); LOAD(retro_unserialize);
    LOAD(retro_get_memory_data); LOAD(retro_get_memory_size);

    struct retro_system_info info = {0};
    p_retro_get_system_info(&info);
    if (argc == 2) {
        printf("%s %s: %s\n", info.library_name, info.library_version, info.valid_extensions);
        dlclose(handle);
        return 0;
    }
    p_retro_set_environment(environment); p_retro_set_video_refresh(video);
    p_retro_set_audio_sample(audio); p_retro_set_audio_sample_batch(batch);
    p_retro_set_input_poll(poll); p_retro_set_input_state(input);
    p_retro_init();
    FILE *file = fopen(argv[2], "rb");
    if (!file || fseek(file, 0, SEEK_END)) return 5;
    long length = ftell(file);
    if (length < 1 || fseek(file, 0, SEEK_SET)) return 5;
    void *rom = malloc(length);
    if (!rom || fread(rom, 1, length, file) != (size_t)length) return 5;
    fclose(file);
    struct retro_game_info game = {.path = argv[2], .data = rom, .size = length};
    if (!p_retro_load_game(&game)) { fprintf(stderr, "Game rejected by %s\n", info.library_name); return 6; }
    for (unsigned i = 0; i < 60; ++i) p_retro_run();
    if (argc > 3 && !strcmp(argv[3], "sram-marker")) {
        const uint8_t *ram = p_retro_get_memory_data(RETRO_MEMORY_SAVE_RAM);
        if (!ram || !p_retro_get_memory_size(RETRO_MEMORY_SAVE_RAM) || ram[0] != 0x5a) {
            fprintf(stderr, "%s did not execute the SRAM store\n", info.library_name); return 7;
        }
    }
    size_t size = p_retro_serialize_size();
    void *state = malloc(size);
    if (!size || !state || !p_retro_serialize(state, size)) return 8;
    for (unsigned i = 0; i < 5; ++i) p_retro_run();
    if (!p_retro_unserialize(state, size)) return 9;
    for (unsigned i = 0; i < 5; ++i) p_retro_run();
    printf("%s: %u frames, %u coloured frames, %zu samples; %zu-byte save state restored.\n",
           info.library_name, frames, coloured, samples, size);
    p_retro_unload_game(); p_retro_deinit();
    free(state); free(rom);
    for (unsigned i = 0; i < option_count; ++i) { free(options[i].key); free(options[i].value); }
    dlclose(handle);
    return frames >= 10 && coloured >= 5 && samples > 0 ? 0 : 12;
}
