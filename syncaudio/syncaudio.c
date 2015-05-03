#include <shenidam.h>

#include "extract_audio.h"

#define NUM_THREADS 1
#define SRC_CONVERTER SRC_SINC_FASTEST


typedef struct {
    char errmsg[128];
    unsigned int sample_rate;
    int lag_samples;
    float lag_seconds;
} LagEstimationStatus;


typedef struct {
    const char *filename;
    float *averaged_audio_data;
    unsigned int averaged_audio_ptr;
    unsigned int sample_rate;
} AudioExtraction;


static void audio_callback(float *audiodata, size_t audiolen, AVCodecContext *codecCtx, void *extra_data) {
    // read an incoming buffer of float audio data, average the channels, write the results into a buffer
    AudioExtraction *audio_extraction = (AudioExtraction*)extra_data;

    if (audio_extraction->averaged_audio_data == NULL) {
        //TODO: Use realloc, be less stupid
        audio_extraction->averaged_audio_data = malloc(sizeof(float) * 10000000);
    }

    float total;
    for (int i=0;i<audiolen;i+=codecCtx->channels) {
        total = 0;
        for (int j=0;j<codecCtx->channels;j++) {
            total += audiodata[i + j];
        }
        audio_extraction->averaged_audio_data[audio_extraction->averaged_audio_ptr++] = total / codecCtx->channels;
    }
    audio_extraction->sample_rate = codecCtx->sample_rate;
}

static void read_audio_data(AudioExtraction *audio_extraction) {
    audio_extraction->averaged_audio_data = NULL;
    audio_extraction->averaged_audio_ptr = 0;
    extract_audio(audio_extraction->filename, audio_callback, audio_extraction);
}

void estimate_lag(const char* base_audiofile_name, const char* track_audiofile_name, LagEstimationStatus *les) {
    // Try to calculate the lag between base_audiofile_name and track_audiofile_name.
    // Store the answer in seconds and samples, along with some other data, in the
    // LagEstimationStatus struction <les>.
    unsigned int nframes_base, nframes_track;
    AudioExtraction base_audio_extraction, track_audio_extraction;

    base_audio_extraction.filename = base_audiofile_name;
    read_audio_data(&base_audio_extraction);
    nframes_base = base_audio_extraction.averaged_audio_ptr;

    les->sample_rate = base_audio_extraction.sample_rate;
    shenidam_t processor = shenidam_create(base_audio_extraction.sample_rate, NUM_THREADS);
    shenidam_set_resampling_quality(processor, SRC_CONVERTER);
    shenidam_set_base_audio(
        processor,
        FORMAT_SINGLE,
        (void*)base_audio_extraction.averaged_audio_data,
        nframes_base,
        (double)base_audio_extraction.sample_rate
    );

    
    track_audio_extraction.filename = track_audiofile_name;
    read_audio_data(&track_audio_extraction);
    nframes_track = track_audio_extraction.averaged_audio_ptr;
    size_t length;
    int in;
    if (shenidam_get_audio_range(
            processor,
            FORMAT_SINGLE,
            (void*)track_audio_extraction.averaged_audio_data,
            nframes_track,
            (double)track_audio_extraction.sample_rate,
            &in,
            &length)) {
        strcpy(les->errmsg, "ERROR: Error mapping track to base .\n");
    }
    les->lag_samples = in;
    les->lag_seconds = (float)in / base_audio_extraction.sample_rate;
    free(base_audio_extraction.averaged_audio_data);
    free(track_audio_extraction.averaged_audio_data);
}


int main (int argc, char** argv) {
    // This is intended to be called from python via subprocess.check_output(),
    // so it eschews convention and prints a parsable message to stdout, and
    // never returns an error code.
    if (argc != 3) {
        printf("Error: Usage: %s [file1.wav] [file2.wav]\n", argv[0]);
        exit(0);
    }

    LagEstimationStatus les;
    les.lag_seconds = les.lag_samples = 0;
    les.errmsg[0] = 0;
    les.sample_rate = 0;

    estimate_lag(argv[1], argv[2], &les);
    if (les.errmsg[0]) {
        printf("Error: %s\n", les.errmsg);
        exit(1);
    }
//    printf("samplerate: %d\n", les.sample_rate);
    printf("lag = %d samples, %f seconds\n", les.lag_samples, (float)les.lag_seconds);
}
