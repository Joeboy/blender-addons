all : syncaudio
CC = gcc
CFLAGS = -std=c99
LDFLAGS = `pkg-config --libs sndfile fftw3f samplerate`
LDFLAGS += -lfftw3f_threads -lm -L./shenidam/build -lshenidam

syncaudio : syncaudio.o
	$(CC) $^ -o $@ $(LDFLAGS)

syncaudio.o : syncaudio.c
	$(CC) $(CFLAGS) -c $^ -o $@

clean :
	rm -f *.o *.so syncaudio

