typedef struct {
    char errmsg[64];
    unsigned int sample_rate;
    int lag_samples;
    float lag_seconds;
} lagestimationstatus;

void estimate_lag(const char* base_audiofilename, const char* audiofile_1, lagestimationstatus *s);
