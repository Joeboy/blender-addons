#include <math.h>
#include <malloc.h>
#include <string.h>

#include "sndfile.h"

#include "shenidam.h"
#include "syncaudio.h"


#define NUM_THREADS 1
#define SRC_CONVERTER SRC_SINC_FASTEST


static int read_sndfile_average(SNDFILE* sndfile,SF_INFO* info,float** result)
{
    size_t n = (size_t) ceil(info->frames/1024.0);
    float *res = *result =(float*) malloc(sizeof(float)*n*1024);
    float* frame = (float*)malloc(sizeof(float)*info->channels*1024);

    for (int i = 0; i < n;i++)
    {

        sf_readf_float(sndfile,frame,1024);
        for (int k = 0; k < 1024; k++)
        {
            float s = 0;
            for (int j = 0 ; j < info->channels; j++)
            {
                s+=frame[k*info->channels + j];
            }
            res[i*1024+k]=s/info->channels;
        }
    }
    free(frame);
    return 0;
}

void estimate_lag(const char* base_audiofilename, const char* audiofile_1, lagestimationstatus *les) {
    SF_INFO base_info;
    memset(&base_info,0,sizeof(SF_INFO));

    SNDFILE* base = sf_open(base_audiofilename,SFM_READ,&base_info);
    if (base == NULL)
    {
        strcpy(les->errmsg, "Failed to load base audio file");
        return;
    }
    les->sample_rate = base_info.samplerate;
    shenidam_t processor = shenidam_create(base_info.samplerate,NUM_THREADS);
    shenidam_set_resampling_quality(processor,SRC_CONVERTER);
    float* base_b;
    read_sndfile_average(base,&base_info,&base_b);
    shenidam_set_base_audio(processor,FORMAT_SINGLE,(void*)base_b,base_info.frames,(double)base_info.samplerate);
    free(base_b);

    size_t length;
    int in;
    SF_INFO track_info;
    memset(&track_info,0,sizeof(SF_INFO));
    float* track_b;
    SNDFILE* track = sf_open(audiofile_1,SFM_READ,&track_info);
    read_sndfile_average(track,&track_info,&track_b);
    sf_close(track);
    if (shenidam_get_audio_range(processor,FORMAT_SINGLE,(void*)track_b,track_info.frames,(double)track_info.samplerate,&in,&length))
    {
        strcpy(les->errmsg, "ERROR: Error mapping track to base .\n");
        free(track);
    }
    les->lag_samples = in;
    les->lag_seconds = (float)in / base_info.samplerate;
    return;
}

int main (int argc, char** argv) {
    // This is intended to be called from python via subprocess.check_output,
    // so it eschews convention and prints a parsable message to stdout, and
    // never returns an error code.
    if (argc != 3) {
        printf("Error: Usage: %s [file1.wav] [file2.wav]\n", argv[0]);
        exit(0);
    }

    lagestimationstatus les;
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
