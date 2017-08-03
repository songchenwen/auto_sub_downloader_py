#!/usr/bin/env python
import os
import sys
from subtitle_utils import convert_ass_to_srt, check_subtitle_file, try_to_fix_subtitle_file
from args import need_srt
from core import SubHDDownloader
from compressor import ZIPFileHandler, RARFileHandler
from sanitizer import to_unicode, to_chs, to_cht, reset_index, set_utf8_without_bom

COMPRESSPR_HANDLER = {
    'rar': RARFileHandler,
    'zip': ZIPFileHandler
}

CHICONV = {
    'zhs': to_chs,
    'zht': to_cht
}

DOWNLOADER = SubHDDownloader()


def choose_subtitle(subs):
    for sub in subs:
        if sub.get('org', None) is not None:
            return sub


def get_subtitle(filename, chiconv_type='zht'):
    if not os.path.isfile(os.path.realpath(filename)):
        sys.stderr.write("File %s not found.\n" % filename)
        sys.exit(1)
    name = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    print('processing %s' % name)

    results = DOWNLOADER.search(name)
    if not results:
        print "No subtitle for %s" % filename
        return [], None

    target = choose_subtitle(results)

    org = target['org']

    print('%s sub for %s' % (org, name))

    # Download sub here.
    datatype, sub_data = DOWNLOADER.download(target.get('id'))
    if sub_data is None:
        print('Can not download sub for %s' % name)
        return [], None
    file_handler = COMPRESSPR_HANDLER.get(datatype)
    compressor = file_handler(sub_data)

    subtitle = {}
    subtitle['name'], subtitle['body'] = compressor.extract_bestguess()
    subtitle['name'] = './' + subtitle['name'].split('/')[-1]
    subtitle['extension'] = subtitle['name'].split('.')[-1]

    # Chinese conversion
    subtitle['body'] = to_unicode(subtitle['body']) # Unicode object
    conv_func = CHICONV.get(chiconv_type)
    subtitle['body'] = conv_func(subtitle['body'])

    if subtitle['extension'] == 'srt':
        subtitle['body'] = reset_index(subtitle['body'])

    subtitle['body'] = set_utf8_without_bom(subtitle['body']) # Plain string
    subtitle['body'] = subtitle['body'].replace('\r\n', '\n') # Unix-style line endings

    basename = os.path.splitext(filename)[0]

    ext = subtitle['extension']

    out_file = "%s.chi.%s" % (basename, ext)
    with open(out_file, 'w') as subfile:
        subfile.write(subtitle['body'])

    subs = []
    checked = check_subtitle_file(out_file)
    if not checked:
        checked = try_to_fix_subtitle_file(out_file)

    if checked:
        subs.append(out_file)
    else:
        return [], None

    if str(ext).lower() == "ass" and need_srt:
        srt_filename = convert_ass_to_srt(out_file)
        if srt_filename is not None:
            subs.insert(0, srt_filename)

    return subs, org
