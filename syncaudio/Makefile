CC = gcc
CFLAGS = -std=c99 -Wall
LDFLAGS = `pkg-config --libs libavformat libavcodec libavutil`
LDFLAGS += -lm -lshenidam

all : syncaudio avfile2wav

syncaudio : syncaudio.o extract_audio.o
	$(CC) $^ -o $@ $(LDFLAGS)

avfile2wav : avfile2wav.o extract_audio.o
	$(CC) $^ -o $@ $(LDFLAGS) `pkg-config --libs sndfile`

syncaudio.o : syncaudio.c
	$(CC) $(CFLAGS) -c $^ -o $@

extract_audio.o : extract_audio.c
	$(CC) $(CFLAGS) -c $^ -o $@

clean :
	rm -f *.o syncaudio avfile2wav

