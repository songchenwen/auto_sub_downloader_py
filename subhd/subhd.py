#!/usr/bin/env python
#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
from subtitle_utils import convert_ass_to_srt, check_subtitle_file, try_to_fix_subtitle_file
from args import need_srt
from core import SubHDDownloader
from compressor import ZIPFileHandler, RARFileHandler
from sanitizer import to_unicode, to_chs, to_cht, reset_index, set_utf8_without_bom
import re

COMPRESSPR_HANDLER = {
    'rar': RARFileHandler,
    'zip': ZIPFileHandler
}

CHICONV = {
    'zhs': to_chs,
    'zht': to_cht
}

DOWNLOADER = SubHDDownloader()

known_orgs = [u'YYeTs字幕组', u'伊甸园字幕组', u'深影字幕组', u'F.I.X字幕侠', u'ZiMuZu字幕组', u'Orange字幕组', u'风软字幕组', u'衣柜字幕组']
required_features = [u'双语', u'ASS']
name_seperator_re = '\.|\s|-|[|]'


def choose_subtitle(subs, name):
    target = None
    for sub in subs:
        sub['score'] = sub_score(sub, name)
        if sub['score'] > 0:
            if target is None or sub['score'] > target['score']:
                target = sub
    return target


def sub_score(sub, name):
    org = sub.get('org', None)
    if org is None:
        return 0
    if org not in known_orgs:
        return 0
    features = sub['features']
    for f in required_features:
        if f not in features:
            return 0
    name = os.path.splitext(name)[0]
    components = re.split(name_seperator_re, name)
    filename = sub.get('filename', None)
    if filename is None:
        return 0
    extra_filename = filename
    for component in components:
        if component not in filename:
            return 0
        else:
            extra_filename = extra_filename.replace(component, '')
    extra_filename = re.sub(name_seperator_re, '', extra_filename)
    org_score = float(len(known_orgs) - known_orgs.index(org)) / float(len(known_orgs)) * 20.0
    feature_score = float(min(len(features), 20.0)) / 20.0 * 40.0
    filename_extra_score = float(min(len(extra_filename), 100.0)) / 100.0 * 10.0 + 10.0
    return org_score + feature_score + filename_extra_score


def get_subtitle(filename, chiconv_type='zht'):
    if not os.path.isfile(os.path.realpath(filename)):
        sys.stderr.write("File %s not found.\n" % filename)
        sys.exit(1)
    name = os.path.basename(filename)
    print('processing %s' % name)

    results = DOWNLOADER.search(name)
    if not results:
        print "No subtitle for %s" % name
        return [], None

    target = choose_subtitle(results, name)
    if target is None:
        print "Score low sub for %s" % name
        return [], None

    org = target['org']

    print('%s %s sub for %s' % (org, ','.join(target['features']), name))

    # Download sub here.
    datatype, sub_data = DOWNLOADER.download(target.get('id'))
    if sub_data is None:
        print('Can not download sub for %s' % name)
        return [], org
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
        return [], org

    if str(ext).lower() == "ass" and need_srt:
        srt_filename = convert_ass_to_srt(out_file)
        if srt_filename is not None:
            subs.insert(0, srt_filename)

    return subs, org
