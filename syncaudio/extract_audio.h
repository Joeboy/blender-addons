#ifndef AVDECODE_H
#define AVDECODE_H

#include <libavformat/avformat.h>

int extract_audio(char *input_filename,
                void (*audio_callback)(float*, size_t, AVCodecContext*, void*),
                void *user_data);
#endif
