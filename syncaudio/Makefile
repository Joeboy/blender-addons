all : syncaudio
CC = gcc
CFLAGS = -std=c99
LDFLAGS = `pkg-config --libs sndfile fftw3f samplerate libavformat libavcodec libavutil`
LDFLAGS += -lfftw3f_threads -lm -L./shenidam/build -lshenidam

syncaudio : syncaudio.o
	$(CC) $^ -o $@ $(LDFLAGS)

avfile2wav : extract_audio.o avfile2wav.o
	$(CC) $^ -o $@ $(LDFLAGS)

syncaudio.o : syncaudio.c
	$(CC) $(CFLAGS) -c $^ -o $@

extract_audio.o : extract_audio.c
	$(CC) $(CFLAGS) -c $^ -o $@

clean :
	rm -f *.o *.so syncaudio

