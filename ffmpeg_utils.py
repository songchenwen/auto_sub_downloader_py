import os
from collections import OrderedDict
from ffmpy import FFmpeg
from args import need_aac
from log_utils import normalize_log_filename
import subprocess
import shlex
import json

debug = False
aac_codec = 'aac'

def combine_file(filename, subs, output):
    inputs_dict = [(filename, None)]
    out_params = ['-map 0:v', '-map 0:a', '-c:v copy', '-c:s copy', '-c:a copy']

    if need_aac:
        audio_streams = get_audio_steams(filename)
        if not has_aac_audio(audio_streams):
            print("convert audio to aac for %s" % normalize_log_filename(filename))
            convert_audio_to_aac(audio_streams, inputs_dict, out_params)

    for i in range(0, len(subs)):
        sub = subs[i]        
        inputs_dict.append((sub, None))
        ext = os.path.splitext(sub)[1]
        out_params.append("-map %d" % (i + 1))
        out_params.append("-metadata:s:s:%d language=chi" % i)
        out_params.append("-metadata:s:s:%d title=chi.%d%s" % (i, i + 1, ext))
    out_params.append('-map 0:s?')
    out_params = " ".join(out_params)

    inputs_dict = OrderedDict(inputs_dict)

    ff = FFmpeg(
        inputs=inputs_dict,
        outputs={output: out_params}
        )
    print(ff.cmd)
    try:
        devnull = open(os.devnull, 'w')
        ff.run(stderr=devnull if not debug else None)
        devnull.close()
        return output
    except Exception as e:
        print(e)
        return None

def get_audio_steams(filename):
    cmd = 'ffprobe -show_streams -select_streams a -loglevel quiet -print_format json'
    args = shlex.split(cmd)
    args.append(filename)
    ffprobe_output = subprocess.check_output(args).decode('utf-8')
    ffprobe_output = json.loads(ffprobe_output)
    return ffprobe_output.get('streams', [])


def has_aac_audio(audio_streams):
    for s in audio_streams:
        codec = s.get('codec_name', '')
        if 'aac' in codec:
            return True
    return False

def convert_audio_to_aac(audio_streams, inputs_dict, out_params):
    source_streams = select_source_audio_streams(audio_streams)
    if len(source_streams) == 0:
        return
    out_params.remove('-c:a copy')
    for i in range(0, len(audio_streams)):
        out_params.append('-codec:a:%d copy' % i)

    for i in range(0, len(source_streams)):
        s = source_streams[i]
        index = s['index']
        tags = s.get('tags', {})
        out_params.append('-map 0:%d' % index)
        out_params.append('-codec:a:%d %s' % (i + len(audio_streams), aac_codec))
        for k, v in tags.iteritems():
            out_params.append('-metadata:s:a:%d %s=%s' % (i + len(audio_streams), k, v))


def select_source_audio_streams(audio_streams):
    languages = []
    none_language = False
    streams = []
    for s in audio_streams:
        tags = s.get('tags', {})
        language = tags.get('language', None)
        if language is None:
            if not none_language:
                streams.append(s)
                none_language = True
        else:
            language = str(language)
            if language not in languages:
                languages.append(language)
                streams.append(s)
    return streams
