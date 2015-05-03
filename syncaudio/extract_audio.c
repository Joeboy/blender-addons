#include <stdio.h>
#include <libavformat/avformat.h>


#define AVCODEC_MAX_AUDIO_FRAME_SIZE 192000


static void die(const char *msg){
    printf("%s\n",msg);
    exit(-1);
}


int extract_audio(const char *input_filename,
                void (*audio_callback)(float*, size_t, AVCodecContext*, void*),
                void *user_data) {
    // Read <input_filename>, which should be an audio or video file containing
    // at least one audio stream.
    // Decode the first audio stream from it, and pass the resulting info to
    // audio_callback.
    // See avfile2wav.c for example usage.

    av_register_all();

    AVFormatContext* pFormatCtx=avformat_alloc_context();
    if(avformat_open_input(&pFormatCtx,input_filename,NULL,NULL)<0){
        die("Could not open file");
    }

    if(avformat_find_stream_info(pFormatCtx, NULL)<0){
        die("Could not find file info");
    }

    //av_dump_format(pFormatCtx,0,input_filename,0);

    // Find first audio stream:
    int audio_stream_id=-1;
    int i;
    for(i=0;i<pFormatCtx->nb_streams;i++){
        if(pFormatCtx->streams[i]->codec->codec_type==AVMEDIA_TYPE_AUDIO){
            audio_stream_id=i;
            break;
        }
    }
    if(audio_stream_id==-1){
        die("Could not find Audio Stream");
    }

//    AVDictionary *metadata=pFormatCtx->metadata;

    AVCodecContext *pCodecCtx=pFormatCtx->streams[audio_stream_id]->codec;
    AVCodec *codec=avcodec_find_decoder(pCodecCtx->codec_id);

    if(codec==NULL){
        die("cannot find codec!");
    }

    if(avcodec_open2(pCodecCtx,codec,NULL)<0){
        die("Codec cannot be opened");
    }

    AVPacket packet;
    av_init_packet(&packet);

    AVFrame *frame=av_frame_alloc();

    int buffer_size=AVCODEC_MAX_AUDIO_FRAME_SIZE + FF_INPUT_BUFFER_PADDING_SIZE;

    uint8_t *buffer = malloc(buffer_size * sizeof(uint8_t));
    packet.data=buffer;
    packet.size =buffer_size;

    int frameFinished=0;
    int plane_size;
    float *out = malloc(buffer_size);
    int write_p;

    while(av_read_frame(pFormatCtx,&packet)>=0) {
        if(packet.stream_index==audio_stream_id){

            avcodec_decode_audio4(pCodecCtx,frame,&frameFinished,&packet);
            av_samples_get_buffer_size(&plane_size, pCodecCtx->channels,
                                                frame->nb_samples,
                                                pCodecCtx->sample_fmt, 1);

            if(frameFinished){
                write_p=0;

                switch (pCodecCtx->sample_fmt){
                    case AV_SAMPLE_FMT_S16P:
                        // Can't find an S16P file to test, so this may or may not work.
                        for (int nb=0;nb<plane_size/sizeof(uint16_t);nb++) {
                            for (int ch = 0; ch < pCodecCtx->channels; ch++) {
                                out[write_p++] = ((uint16_t *) frame->extended_data[ch])[nb] / SHRT_MAX;
                            }
                        }
                        break;
                    case AV_SAMPLE_FMT_FLTP:
                        for (int nb=0;nb<plane_size/sizeof(float);nb++){
                            for (int ch = 0; ch < pCodecCtx->channels; ch++) {
                                out[write_p++] = ((float *) frame->extended_data[ch])[nb];
                            }
                        }
                        break;
                    case AV_SAMPLE_FMT_S16:
                        for (int nb=0;nb<plane_size/sizeof(short);nb++){
                            out[write_p++] = (float) ((short*) frame->extended_data[0])[nb] / SHRT_MAX;
                        }
                        break;
                    case AV_SAMPLE_FMT_FLT:
                        for (int nb=0;nb<plane_size/sizeof(float);nb++){
                            out[write_p++] = (float) ((float*)frame->extended_data[0])[nb];
                        }
                        break;
                    case AV_SAMPLE_FMT_U8P:
                        // totally untested...
                        for (int nb=0;nb<plane_size/sizeof(uint8_t);nb++){
                            for (int ch = 0; ch < pCodecCtx->channels; ch++) {
                                out[write_p++] = ( (int8_t)(((uint8_t *) frame->extended_data[ch])[nb]) - 127) / SCHAR_MAX;
                            }
                        }
                        break;
                    case AV_SAMPLE_FMT_U8:
                        for (int nb=0;nb<plane_size/sizeof(uint8_t);nb++){
                            out[write_p++] = ((float) (((uint8_t*)frame->extended_data[0])[nb]) - 127) / SCHAR_MAX;
                        }
                        break;
                    default:
                        die("PCM type not supported");

                }
                if (audio_callback) (*audio_callback)(out, write_p, pCodecCtx, user_data);
            } else {
                die("frame failed");
            }
        }
        av_free_packet(&packet);
    }

    avcodec_close(pCodecCtx);
    avformat_free_context(pFormatCtx);
    av_frame_free(&frame);
    free(buffer);
    free(out);
    return 0;
}
