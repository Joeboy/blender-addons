all : libsyncaudio.so
CC = gcc
CFLAGS = -std=c99
LDFLAGS = `pkg-config --libs sndfile fftw3f samplerate`
LDFLAGS += -lfftw3f_threads -lm

syncaudio : syncaudio.o shenidam.o
	$(CC) $^ -o $@ $(LDFLAGS)

syncaudio.o : syncaudio.c
	$(CC) $(CFLAGS) -fPIC -c $^ -o $@

shenidam.o : shenidam.c
	$(CC) $(CFLAGS) -fPIC -c $^ -o $@

clean :
	rm -f *.o *.so syncaudio

