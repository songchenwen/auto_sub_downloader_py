import os
from log_utils import normalize_log_filename
import asstosrt
import subprocess
import shlex
import json
import re


def convert_ass_to_srt(ass_filename):
    ass_file = open(ass_filename)
    srt_filename = "%s.srt" % os.path.splitext(ass_filename)[0]
    print('converting %s to %s' % (normalize_log_filename(ass_filename), normalize_log_filename(srt_filename)))
    srt_file = open(srt_filename, 'w')
    try:
        srt_str = asstosrt.convert(ass_file)
        srt_file.write(srt_str.encode("UTF8"))
    except Exception as e:
        print("converting srt error %s" % e.message)
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


def try_to_fix_subtitle_file(filename):
    ext = os.path.splitext(filename)[1]
    if str(ext).lower() == '.ass':
        return try_to_fix_ass_file(filename)
    if str(ext).lower() == '.srt':
        return try_to_fix_srt_file(filename)
    return False


def try_to_fix_ass_file(filename):
    ext = os.path.splitext(filename)[1]
    if str(ext).lower() != '.ass':
        return False
    contents = None
    ass_file = open(filename, 'r')
    try:
        contents = ass_file.read()
        contents = unicode(contents)
        ass_file.close()
    except Exception as e:
        print(e)
        ass_file.close()
        return False

    first_line = contents.splitlines()[0]
    if first_line.strip() != "[Script Info]":
        print('try to fix ass file %s' % filename)
        contents = contents.replace(first_line, "[Script Info]", 1)
        ass_file = open(filename, 'w')
        try:
            ass_file.write(contents.encode('utf-8'))
            ass_file.close()
            return check_subtitle_file(filename)
        except Exception as e:
            print(e)
            ass_file.close()
            return False
    return False


def try_to_fix_srt_file(filename):
    ext = os.path.splitext(filename)[1]
    if str(ext).lower() != '.srt':
        return False
    contents = None
    srt_file = open(filename, 'r')
    try:
        contents = srt_file.read()
        contents = unicode(contents)
        srt_file.close()
    except Exception as e:
        print(e)
        srt_file.close()
        return False

    content_lines = contents.splitlines(True)

    line1_exp = re.compile(r'^[0-9]+\s*$')
    line2_exp = re.compile(r'^\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}\s*$')

    found_beginning = False
    beginning_line = 0
    while not found_beginning:
        if (beginning_line + 2) >= len(content_lines):
            return False
        line1 = content_lines[beginning_line]
        line2 = content_lines[beginning_line + 1]
        line3 = content_lines[beginning_line + 2]
        line1_good = line1_exp.match(line1)
        if line1_good:
            line2_good = line2_exp.match(line2)
            if line2_good:
                line3_good = len(line3.strip()) > 0
                if line3_good:
                    found_beginning = True
        if not found_beginning:
            beginning_line = beginning_line + 1

    if found_beginning:
        print('try to fix srt %s' % filename)
        contents = ''.join(content_lines[beginning_line:])
        srt_file = open(filename, 'w')
        try:
            srt_file.write(contents.encode('utf-8'))
            srt_file.close()
            return check_subtitle_file(filename)
        except Exception as e:
            print(e)
            srt_file.close()
            return False

    return False
