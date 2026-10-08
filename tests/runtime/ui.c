// SPDX-License-Identifier: GPL-2.0-only
// Drive the unmodified frontend through SDL events in an isolated test root.
#include <SDL2/SDL.h>
#include <GLES2/gl2.h>
#include <dlfcn.h>
#include <png.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static unsigned frame, next, count;
static int loaded, release_key;
static struct { unsigned frame; char command[32]; } actions[128];

static void load(void) {
    if (loaded) return;
    loaded = 1;
    FILE *file = fopen("/test/actions", "r");
    if (!file) exit(20);
    while (count < 128 && fscanf(file, "%u %31s", &actions[count].frame, actions[count].command) == 2)
        ++count;
    fclose(file);
}

static void capture(SDL_Window *window) {
    int width, height;
    SDL_GL_GetDrawableSize(window, &width, &height);
    if (width != 640 || height != 480) exit(21);
    unsigned char *pixels = malloc(width * height * 4);
    glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
    if (glGetError() != GL_NO_ERROR) exit(22);
    unsigned visible = 0;
    for (int i = 0; i < width * height; ++i)
        if (pixels[i * 4] || pixels[i * 4 + 1] || pixels[i * 4 + 2]) ++visible;
    if (visible < 1000) { fprintf(stderr, "Blank UI frame %u\n", frame); exit(27); }
    char path[80];
    snprintf(path, sizeof(path), "/test/frame-%03u.png", frame);
    FILE *file = fopen(path, "wb");
    if (!file) exit(23);
    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info = png_create_info_struct(png);
    if (!png || !info || setjmp(png_jmpbuf(png))) exit(24);
    png_init_io(png, file);
    png_set_IHDR(png, info, width, height, 8, PNG_COLOR_TYPE_RGBA,
                 PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_write_info(png, info);
    for (int y = height - 1; y >= 0; --y) png_write_row(png, pixels + y * width * 4);
    png_write_end(png, info);
    png_destroy_write_struct(&png, &info);
    fclose(file);
    free(pixels);
}

void SDL_GL_SwapWindow(SDL_Window *window) {
    void (*real_swap)(SDL_Window *) = dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
    load();
    ++frame;
    if (next < count && actions[next].frame <= frame && !strcmp(actions[next].command, "capture")) {
        capture(window);
        ++next;
    }
    real_swap(window);
    SDL_Delay(80); // Let real frontend transitions finish between input events.
}

int SDL_PollEvent(SDL_Event *event) {
    int (*real_poll)(SDL_Event *) = dlsym(RTLD_NEXT, "SDL_PollEvent");
    if (!event) return real_poll(event);
    load();
    int key = 0;
    if (release_key) {
        key = release_key;
        release_key = 0;
        memset(event, 0, sizeof(*event));
        event->type = SDL_KEYUP;
    } else if (next < count && actions[next].frame <= frame && strcmp(actions[next].command, "capture")) {
        const char *command = actions[next++].command;
        memset(event, 0, sizeof(*event));
        if (!strcmp(command, "quit")) { event->type = SDL_QUIT; return 1; }
        if (!strcmp(command, "remove-game")) {
            if (unlink("/easyroms/gb/runtime.gb")) exit(26);
            return real_poll(event);
        }
        key = SDL_GetKeyFromName(command);
        if (!key) exit(25);
        release_key = key;
        event->type = SDL_KEYDOWN;
        event->key.state = SDL_PRESSED;
    } else {
        return real_poll(event);
    }
    event->key.keysym.sym = key;
    event->key.keysym.scancode = SDL_GetScancodeFromKey(key);
    event->key.timestamp = SDL_GetTicks();
    return 1;
}
