import os
import shutil
from args import debug

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


def clear_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
