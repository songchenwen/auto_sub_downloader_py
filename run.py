#!/usr/bin/env python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
print("defaultencoding %s" % sys.getdefaultencoding())

import hashlib
import os
import shutil
import requests
from requests.packages.urllib3 import disable_warnings
from collections import OrderedDict
from ffmpy import FFmpeg
import asstosrt
import opencc
import time

wanted_exts = ['.mp4', '.mkv']
ignore_filenames = ['rarbg.mp4']
opencc_config = 'tw2sp.json'
tmp_dir = str(os.environ.get('TMP_DIR', '/tmp/sub_downloader'))


def calculate_checksum(filename):
    """
    calculate the checksum of the file as was used by shooter.cn.
    The whole idea is to sample four parts (start, one third, two thirds,
    end ) of the video file, and calculate their checksum individually.
    """
    offset = 4096
    fobj = open(filename)
    def md5(position, whence=0):
        m = hashlib.md5()
        fobj.seek(position, whence)
        m.update(fobj.read(offset))
        return m.hexdigest()

    fobj.seek(0, 2)
    filesize = fobj.tell()

    checksum =  ';'.join(
        [md5(offset), md5(filesize/3 * 2), md5(filesize/3), md5(-2*offset, 2)]
    )
    fobj.close()
    return checksum

def get_subtitleinfo(filename):
    """do api request, parse error, return response."""
    response = requests.post(
        "https://www.shooter.cn/api/subapi.php",
        verify=False,
        params= {
            'filehash': calculate_checksum(filename),
            'pathinfo': os.path.realpath(filename),
            'format': 'json',
            'lang': "chi",
        },
    )
    if response.text == u'\xff':
        sys.stderr.write("Subtitle not found.\n")
        return None
    return response

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def download_subtitle(filename):
    disable_warnings()
    if not os.path.isfile(os.path.realpath(filename)):
        sys.stderr.write("File %s not found.\n" % filename)
        sys.exit(1)
    print('processing %s' % normalize_log_filename(filename))
    basename = os.path.splitext(filename)[0]
    response = get_subtitleinfo(filename)
    if response is None:
        return []
    
    subtitles = []
    subtitle_contents = set([])
    srt_count = 0
    for count in xrange(len(response.json())):

        for fileinfo in response.json()[count]['Files']:
            url = fileinfo['Link']
            ext = fileinfo['Ext']
            _response = requests.get(url, verify=False)

            if _response.ok and _response.text not in subtitle_contents:
                if check_contain_chinese(_response.text):
                    if len(subtitles) == 0:
                        _basename = "%s.chi" % (basename)
                    else:
                        _basename = "%s.chi.%s" % (basename, len(subtitles))

                    _filename = "%s.%s" % (_basename, ext)
                    subtitle_contents.add(_response.text)
                    subtitles.append(_filename)
                    if str(ext).lower() == 'srt':
                        srt_count = srt_count + 1
                    fobj = open(_filename, 'w')
                    fobj.write(opencc.convert(_response.text, config=opencc_config).encode("UTF8"))
                    fobj.close()

    if len(subtitles) > 0:
        if srt_count == 0:
            srt_filename = convert_ass_to_srt(subtitles[0])
            if srt_filename is not None:
                subtitles.append(srt_filename)
        print("%d subtitles for %s" % (len(subtitles), normalize_log_filename(filename)))
    else:
        print("no subtitles for %s" % normalize_log_filename(filename))

    return subtitles

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

def normalize_log_filename(filename):
    return os.path.basename(filename)

def combine_file(filename, subs, output):
    inputs_dict = [(filename, None)]
    out_params = ['-map 0:v', '-map 0:a']

    for i in range(0, len(subs)):
        sub = subs[i]        
        inputs_dict.append((sub, None))
        ext = os.path.splitext(sub)[1]
        out_params.append("-map %d" % (i + 1))
        out_params.append("-metadata:s:s:%d language=chi" % i)
        out_params.append("-metadata:s:s:%d title=chi.%d%s" % (i, i + 1, ext))
    out_params.extend(['-map 0:s?', '-c copy'])
    out_params = " ".join(out_params)

    inputs_dict = OrderedDict(inputs_dict)

    ff = FFmpeg(
        inputs=inputs_dict,
        outputs={output: out_params}
        )
    print(ff.cmd)
    try:
        devnull = open(os.devnull, 'w')
        ff.run(stderr=devnull)
        devnull.close()
        return output
    except Exception as e:
        print(e)
        return None

def clean_origin_files(filename, subs):
    os.remove(filename)
    for sub in subs:
        os.remove(sub)

def clean_empty_folders(dir):
    for root, subdirs, files in os.walk(dir, topdown=False):
        root_deleted = False
        for name in files:
            if not is_file_wanted(name):
                os.remove(os.path.join(root, name))
            if root != dir:
                if len(os.listdir(root)) == 0:
                    root_deleted = True
                    os.rmdir(root)
        if (not root_deleted) and root != dir:
            if len(os.listdir(root)) == 0:
                os.rmdir(root)

def is_file_wanted(filename):
    basename = os.path.basename(filename)
    if str(basename).lower() in ignore_filenames:
        return False
    parts = os.path.splitext(filename)
    if len(parts) > 0:
        ext = parts[1]
        if str(ext).lower() in wanted_exts:
            return True
    return False

def main():
    input_dir = None
    output_dir = None
    if len(sys.argv) > 1:
        input_dir = str(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = str(sys.argv[2])
    if input_dir is None:
        input_dir = str(os.environ.get('INPUT', '/input'))
    if output_dir is None:
        output_dir = str(os.environ.get('OUTPUT', '/output'))
    interval = float(os.environ.get('INTERVAL', 0))
    print('from %s to %s interval %f' % (input_dir, output_dir, interval))
    should_loop = True
    while should_loop:
        for root, dirs, files in os.walk(input_dir):
            for name in files:
                filename = os.path.join(root, name)
                parts = os.path.splitext(filename)
                if is_file_wanted(filename):
                    subs = download_subtitle(filename)
                    if len(subs) > 0:
                        basename = os.path.splitext(os.path.basename(filename))[0]
                        outfilename = "%s.chi.mkv" % basename
                        tmpname = combine_file(filename, subs, os.path.join(tmp_dir, outfilename))
                        if tmpname is not None:
                            shutil.move(tmpname, os.path.join(output_dir, outfilename))
                            clean_origin_files(filename, subs)
        clean_empty_folders(input_dir)
        print('clean folder %s' % input_dir)
        should_loop = (interval > 0)
        if should_loop:
            print('sleep %fs' % interval)
            time.sleep(interval)

if __name__ == '__main__':
    main()
