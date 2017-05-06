#!/usr/bin/env python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
print("defaultencoding %s" % sys.getdefaultencoding())
import os
import shutil
import time

from cleaner import is_file_wanted, clean_origin_files, clean_empty_folders
from shooter import download_subtitle
from ffmpeg_utils import combine_file


tmp_dir = str(os.environ.get('TMP_DIR', '/tmp/sub_downloader'))

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
