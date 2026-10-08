// SPDX-License-Identifier: GPL-2.0-only
#include "ImageIO.h"
#include <SDL_image.h>
#include <webp/encode.h>
#include <cassert>
#include <fstream>
#include <iterator>
#include <limits>
#include <string>
#include <vector>

static std::vector<unsigned char> read(const std::string& path)
{
	std::ifstream input(path, std::ios::binary);
	return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}
int main(int argc, char** argv)
{
	assert(argc == 4);
	size_t w, h;
	auto pixel = read(argv[1]);
	auto decoded = ImageIO::loadFromMemoryRGBA32(pixel.data(), pixel.size(), w, h);
	assert(w == 1 && h == 1 && decoded == std::vector<unsigned char>({0x11, 0x22, 0x33, 0xff}));
	auto oversized = read(argv[2]);
	assert(ImageIO::loadFromMemoryRGBA32(oversized.data(), oversized.size(), w, h).empty());
	assert(w == 0 && h == 0);
	assert(ImageIO::loadFromMemoryRGBA32(pixel.data(), std::numeric_limits<size_t>::max(), w, h).empty());
	assert(ImageIO::loadFromMemoryRGBA32(reinterpret_cast<const unsigned char*>("8BPS"), 4, w, h).empty());
	unsigned char rgba[] = {255,0,0,255, 0,255,0,255, 0,0,255,64, 255,255,255,255};
	SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormatFrom(rgba, 2, 2, 32, 8, SDL_PIXELFORMAT_RGBA32);
	assert(surface);
	std::string png = std::string(argv[3]) + "/artwork.png", jpg = std::string(argv[3]) + "/artwork.jpg";
	assert(IMG_SavePNG(surface, png.c_str()) == 0);
	assert(IMG_SaveJPG(surface, jpg.c_str(), 95) == 0);
	SDL_FreeSurface(surface);
	auto bytes = read(png);
	decoded = ImageIO::loadFromMemoryRGBA32(bytes.data(), bytes.size(), w, h);
	assert(w == 2 && h == 2 && decoded.size() == 16);
	assert(std::equal(decoded.begin(), decoded.begin()+8, rgba+8));
	assert(std::equal(decoded.begin()+8, decoded.end(), rgba));
	bytes = read(jpg);
	assert(!ImageIO::loadFromMemoryRGBA32(bytes.data(), bytes.size(), w, h).empty() && w == 2 && h == 2);
	uint8_t* webp = nullptr;
	size_t webp_size = WebPEncodeLosslessRGBA(rgba, 2, 2, 8, &webp);
	assert(webp_size);
	decoded = ImageIO::loadFromMemoryRGBA32(webp, webp_size, w, h);
	WebPFree(webp);
	assert(w == 2 && h == 2 && decoded[2] == 255 && decoded[3] == 64);
	assert(ImageIO::resizeFile(png, 8, 0));
	bytes = read(png);
	assert(!ImageIO::loadFromMemoryRGBA32(bytes.data(), bytes.size(), w, h).empty() && w == 8 && h == 8);
	assert(ImageIO::resizeFile(jpg, 0, 4));
	bytes = read(jpg);
	assert(!ImageIO::loadFromMemoryRGBA32(bytes.data(), bytes.size(), w, h).empty() && w == 4 && h == 4);
	assert(!ImageIO::resizeFile(png, 4097, 4097));
	assert(read(png).size() > 0);
	assert(!ImageIO::resizeFile(png + ".missing", 4, 4));
	SDL_Quit();
	return 0;
}
