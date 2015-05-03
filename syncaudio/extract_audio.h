#ifndef EXTRACT_AUDIO_H
#define EXTRACT_AUDIO_H

#include <libavformat/avformat.h>

int extract_audio(
    const char *input_filename,
    void (*audio_callback)(float*, size_t, AVCodecContext*, void*),
    void *user_data
);

#endif
