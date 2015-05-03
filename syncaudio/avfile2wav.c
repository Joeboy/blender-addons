// Just a dumb example/test for avdecode.c
//
#include "extract_audio.h"
#include <sndfile.h>
#include <libavformat/avformat.h>

typedef struct {
    char *output_filename;
    SNDFILE *sf;
} UserData;

void audio_callback(float *audiodata, size_t audiolen, AVCodecContext *codecCtx, void *extra_data) {
    // Write data to a wav file
    UserData *user_data = (UserData*)extra_data;
    if (user_data->sf == NULL) {
        SF_INFO sf_info;
        sf_info.frames = 1024;
        sf_info.samplerate = codecCtx->sample_rate;
        sf_info.channels = codecCtx->channels;
        sf_info.format = SF_FORMAT_WAV + SF_FORMAT_FLOAT;
        sf_info.sections = 0;
        sf_info.seekable = 0;
        user_data->sf = sf_open(user_data->output_filename, SFM_WRITE, &sf_info);
    }
    sf_write_float(user_data->sf, audiodata, audiolen);
}


int main(int argc, char **argv) {
    if (argc != 3) {
        printf("Usage: %s [input_avfile] [output_wavfile]\n", argv[0]);
        exit(1);
    }
    UserData user_data;
    user_data.output_filename = argv[2];
    user_data.sf = NULL;
    extract_audio(argv[1], audio_callback, &user_data);
    sf_close(user_data.sf);
}

