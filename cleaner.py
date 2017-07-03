import os
import shutil
from args import debug, old_days, sub_available_delay
from log_utils import normalize_log_filename
import datetime

wanted_exts = ['.mp4', '.mkv']
ignore_filenames = ['rarbg.mp4','placeholder.mp4']


def clean_origin_files(filename, subs):
    if debug:
        return
    os.remove(filename)
    for sub in subs:
        os.remove(sub)


def clean_empty_folders(dir):
    if debug:
        return
    for root, subdirs, files in os.walk(dir, topdown=False):
        root_deleted = False
        for name in files:
            if not is_file_wanted(name) and os.path.basename(name).lower() != 'placeholder.mp4':
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


def clean_old_files(dir):
    if old_days <= 0:
        return
    for root, subdirs, files in os.walk(dir):
        for filename in files:
            if is_file_wanted(filename):
                filetime = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(root, filename)))
                if (datetime.datetime.now() - filetime) > datetime.timedelta(days=old_days):
                    print('too old %s' % normalize_log_filename(filename))
                    if not debug:
                        os.remove(os.path.join(root, filename))
                        

def is_sub_available(f):
    filetime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
    return (datetime.datetime.now() - filetime) > datetime.timedelta(days=sub_available_delay)


def clear_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
