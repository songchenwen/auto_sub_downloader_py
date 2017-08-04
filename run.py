#!/usr/bin/env python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
print("defaultencoding %s" % sys.getdefaultencoding())
import os
import shutil
import time

from cleaner import is_file_wanted, clean_origin_files, clean_empty_folders, clear_folder, clean_old_files, is_sub_available
from shooter import download_subtitle
from ffmpeg_utils import combine_file
from args import input_dir, output_dir, interval, throttle
from subhd.subhd import get_subtitle


tmp_dir = str(os.environ.get('TMP_DIR', '/tmp/sub_downloader'))

def main():
    should_loop = True
    while should_loop:
        clear_folder(tmp_dir)
        for root, dirs, files in os.walk(input_dir):
            for name in files:
                filename = os.path.join(root, name)
                parts = os.path.splitext(filename)
                if is_file_wanted(filename):
                    if is_sub_available(filename):
                        subs, org = get_subtitle(filename, chiconv_type='zhs')
                        # subs = download_subtitle(filename)
                        if len(subs) > 0:
                            basename = os.path.splitext(os.path.basename(filename))[0]
                            outfilename = "%s.chi.mkv" % basename
                            tmpname = combine_file(filename, subs, os.path.join(tmp_dir, outfilename), org)
                            if tmpname is not None:
                                shutil.move(tmpname, os.path.join(output_dir, outfilename))
                                clean_origin_files(filename, subs)
                        if org is not None:
                            print('throttle %d' % throttle)
                            time.sleep(throttle)
        clean_old_files(input_dir)
        clean_empty_folders(input_dir)
        print('clean folder %s' % input_dir)
        should_loop = (interval > 0)
        if should_loop:
            print('sleep %fs' % interval)
            time.sleep(interval)

if __name__ == '__main__':
    main()
