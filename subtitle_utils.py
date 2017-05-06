import os
from log_utils import normalize_log_filename
import asstosrt
import subprocess
import shlex
import json

def convert_ass_to_srt(ass_filename):
    ass_file = open(ass_filename)
    srt_filename = "%s.srt" % os.path.splitext(ass_filename)[0]
    print('converting %s to %s' % (normalize_log_filename(ass_filename), normalize_log_filename(srt_filename)))
    srt_file = open(srt_filename, 'w')
    try:
        srt_str = asstosrt.convert(ass_file)
        srt_file.write(srt_str.encode("UTF8"))
    except Exception as e:
        print(e)
        srt_filename = None
    ass_file.close()
    srt_file.close()
    return srt_filename

def check_subtitle_file(filename):
    cmd = 'ffprobe -show_streams -select_streams s -loglevel quiet -print_format json'
    args = shlex.split(cmd)
    args.append(filename)
    try:
        ffprobe_output = subprocess.check_output(args).decode('utf-8')
        ffprobe_output = json.loads(ffprobe_output)
        return len(ffprobe_output.get('streams', [])) > 0
    except subprocess.CalledProcessError as ex:
        return False
