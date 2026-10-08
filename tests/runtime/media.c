// SPDX-License-Identifier: GPL-2.0-only
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/mem.h>
#include <stdio.h>
#include <string.h>

// Original 16x16 red frame encoded as baseline H.264, with encoder SEI removed.
static const unsigned char red[] = {
    0,0,0,1,0x67,0x42,0xc0,0x0a,0xdd,0xec,0x04,0x40,0,0,3,0x00,
    0x40,0,0,0x0c,0x83,0xc4,0x89,0xe0,0,0,0,1,0x68,0xce,0x0f,0x2c,
    0x80,0,0,1,0x65,0x88,0x84,0x04,0xbc,0x46,0x28,0,0x0a,0x8b,
    0xc7,0,1,0x28,0xd8,0xe0,0,0x2f,0xad,0x80
};

int main(void) {
    const enum AVCodecID required[] = { AV_CODEC_ID_H264, AV_CODEC_ID_ATRAC3,
        AV_CODEC_ID_ATRAC3P, AV_CODEC_ID_AAC, AV_CODEC_ID_MP3 };
    for (unsigned i = 0; i < sizeof(required) / sizeof(required[0]); ++i)
        if (!avcodec_find_decoder(required[i])) { fprintf(stderr, "Missing codec %d\n", required[i]); return 1; }
    const char *formats[] = { "mpeg", "oma", "pmp" };
    for (unsigned i = 0; i < sizeof(formats) / sizeof(formats[0]); ++i)
        if (!av_find_input_format(formats[i])) { fprintf(stderr, "Missing format %s\n", formats[i]); return 2; }
    const AVCodec *codec = avcodec_find_decoder(AV_CODEC_ID_H264);
    AVCodecContext *context = avcodec_alloc_context3(codec);
    if (!context || avcodec_open2(context, codec, NULL) < 0) return 3;
    AVPacket *packet = av_packet_alloc();
    AVFrame *frame = av_frame_alloc();
    if (!packet || !frame || av_new_packet(packet, sizeof(red)) < 0) return 4;
    memcpy(packet->data, red, sizeof(red));
    if (avcodec_send_packet(context, packet) < 0 || avcodec_receive_frame(context, frame) < 0) return 5;
    if (frame->width != 16 || frame->height != 16 || frame->format != AV_PIX_FMT_YUV420P ||
        frame->data[0][0] < 70 || frame->data[0][0] > 90 ||
        frame->data[1][0] < 80 || frame->data[1][0] > 100 || frame->data[2][0] < 230) return 6;
    av_frame_free(&frame);
    av_packet_free(&packet);
    avcodec_free_context(&context);
    puts("FFmpeg H.264 decode and PSP codec/format checks passed.");
    return 0;
}
