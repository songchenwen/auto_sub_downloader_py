#!/usr/bin/env python
#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
from subtitle_utils import convert_ass_to_srt, check_subtitle_file, try_to_fix_subtitle_file
from args import need_srt, throttle, ip_change_url
from core import SubHDDownloader
from compressor import ZIPFileHandler, RARFileHandler
from sanitizer import to_unicode, to_chs, to_cht, reset_index, set_utf8_without_bom, get_extra_filename, get_search_names
from guessit import guessit
import requests
import time
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

known_orgs = [u'YYeTs字幕组', u'伊甸园字幕组', u'深影字幕组', u'衣柜字幕组', u'F.I.X字幕侠', u'ZiMuZu字幕组', u'Orange字幕组', u'风软字幕组']
required_features = [u'双语', u'ASS']


def choose_subtitle(subs, name):
    results = []
    for sub in subs:
        sub['score'] = sub_score(sub, name)
        if sub['score'] > 0:
            results.append(sub)
    results.sort(key=lambda s: s['score'], reverse=True)
    return results


def sub_score(sub, name):
    guessed = guessit(name)
    type = guessed.get('type', None)
    require_org = type == 'episode'
    require_ass = type == 'episode'
    org = sub.get('org', None)
    if org is None and require_org:
        return 0
    if org not in known_orgs and require_org:
        return 0
    features = sub['features']
    for f in required_features:
        if f == u'ASS' and not require_ass:
            continue
        if f not in features:
            return 0
    name = os.path.splitext(name)[0]
    filename = sub.get('filename', None)
    if filename is None:
        return 0
    extra_filename = get_extra_filename(name, filename)
    if extra_filename is None:
        return 0
    org_score = float((len(known_orgs) + 1 - known_orgs.index(org)) if org in known_orgs else
                      (1 if org is not None else 0)) / float(len(known_orgs) + 1) * 20.0
    feature_score = float(min(len(features), 20.0)) / 20.0 * 20.0
    filename_extra_score = 10.0 - float(min(len(extra_filename), 100.0)) / 100.0 * 10.0
    return org_score + feature_score + filename_extra_score


def get_subtitle(filename, chiconv_type='zht'):
    if not os.path.isfile(os.path.realpath(filename)):
        sys.stderr.write("File %s not found.\n" % filename)
        sys.exit(1)
    name = os.path.basename(filename)
    print('processing %s' % name)

    for search_name in get_search_names(name):
        print('searching for %s' % search_name)
        results = DOWNLOADER.search(search_name)
        if not results:
            print "No subtitle for %s" % name
            continue
        targets = choose_subtitle(results, name)

        if len(targets) == 0:
            print "Score low sub for %s" % name
            continue

        should_throttle = False
        for target in targets:
            if should_throttle:
                time.sleep(throttle)

            org = target.get('org', None)
            if org is not None:
                org = unicode(org)

            print('%s %s %s sub for %s' % (org if org is not None else "no org", ','.join(target['features']),
                                           target['title'] if target.get('title', None) is not None else 'no title', name))

            # Download sub here.
            datatype = None
            sub_data = None

            try_times = 1 if ip_change_url is None else 2

            for i in range(try_times):
                if i > 0:
                    if ip_change_url is not None:
                        print('change ip for %s' % name)
                        try:
                            requests.get(ip_change_url)
                        except Exception:
                            pass
                        time.sleep(30)
                datatype, sub_data = DOWNLOADER.download(target.get('id'))
                if sub_data is not None:
                    break

            if sub_data is None:
                print('Can not download sub for %s' % name)
                should_throttle = True
                continue

            file_handler = COMPRESSPR_HANDLER.get(datatype)
            compressor = file_handler(sub_data)

            subtitle = {}
            subtitle['name'], subtitle['body'] = compressor.extract_bestguess(name)
            if subtitle['name'] is None:
                print('no suitable file to uncompress %s' % name)
                should_throttle = True
                continue

            subtitle['name'] = './' + subtitle['name'].split('/')[-1]
            subtitle['extension'] = subtitle['name'].split('.')[-1]

            # Chinese conversion
            subtitle['body'] = to_unicode(subtitle['body']) # Unicode object
            conv_func = CHICONV.get(chiconv_type)
            subtitle['body'] = conv_func(subtitle['body'])

            if subtitle['extension'] == 'srt':
                subtitle['body'] = reset_index(subtitle['body'])

            # subtitle['body'] = set_utf8_without_bom(subtitle['body']) # Plain string
            # subtitle['body'] = subtitle['body'].replace('\r\n', '\n') # Unix-style line endings

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
                should_throttle = True
                continue

            if str(ext).lower() == "ass" and need_srt:
                srt_filename = convert_ass_to_srt(out_file)
                if srt_filename is not None:
                    subs.insert(0, srt_filename)

            return subs, org
        time.sleep(throttle)
    return [], 'OP_ERROR'
