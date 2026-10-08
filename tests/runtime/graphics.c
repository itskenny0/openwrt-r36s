// SPDX-License-Identifier: GPL-2.0-only
// Exercise the shipped SDL -> EGL -> GLES path and read back actual pixels.
#include <SDL2/SDL.h>
#include <GLES2/gl2.h>
#include <stdio.h>

int main(void) {
    if (SDL_Init(SDL_INIT_VIDEO)) goto fail;
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);
    SDL_Window *window = SDL_CreateWindow("render check", 0, 0, 640, 480, SDL_WINDOW_OPENGL);
    if (!window) goto fail;
    SDL_GLContext context = SDL_GL_CreateContext(window);
    if (!context) goto fail;
    printf("GLES: %s; renderer: %s\n", glGetString(GL_VERSION), glGetString(GL_RENDERER));
    glClearColor(1, 0, 0, 1);
    glClear(GL_COLOR_BUFFER_BIT);
    unsigned char pixel[4] = {0};
    glReadPixels(320, 240, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
    if (glGetError() != GL_NO_ERROR || pixel[0] != 255 || pixel[1] || pixel[2]) return 2;
    SDL_GL_SwapWindow(window);
    SDL_GL_DeleteContext(context);
    SDL_DestroyWindow(window);
    SDL_Quit();
    puts("SDL/EGL/GLES framebuffer readback passed.");
    return 0;
fail:
    fprintf(stderr, "SDL: %s\n", SDL_GetError());
    SDL_Quit();
    return 1;
}
