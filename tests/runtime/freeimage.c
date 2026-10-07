// SPDX-License-Identifier: GPL-2.0-only
#include <FreeImage.h>
#include <stdio.h>
int main(int argc, char **argv) {
    FreeImage_Initialise(0);
    FIBITMAP *bitmap = argc == 2 ? FreeImage_Load(FIF_PNG, argv[1], 0) : NULL;
    RGBQUAD pixel = {0};
    if (!bitmap || FreeImage_GetWidth(bitmap) != 1 || FreeImage_GetHeight(bitmap) != 1 ||
        !FreeImage_GetPixelColor(bitmap, 0, 0, &pixel) ||
        pixel.rgbRed != 0x11 || pixel.rgbGreen != 0x22 || pixel.rgbBlue != 0x33)
        return 1;
    FreeImageIO io = {0};
    if (FreeImage_SaveToHandle(FIF_PSD, bitmap, &io, NULL, 0))
        return 2;
    FreeImage_Unload(bitmap);
    FreeImage_DeInitialise();
    puts("FreeImage: PNG decode and invalid PSD handle passed on aarch64/musl.");
    return 0;
}
