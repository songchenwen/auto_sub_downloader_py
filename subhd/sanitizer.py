#coding=utf-8
'''Few sanitizer functions to process subtitle text.
'''
import chardet
from pyTongwen.conv import TongWenConv
import StringIO
import re
import pysrt
import os

__TONGWEN = TongWenConv()

def to_unicode(sub_str):
    '''Convert plain string to unicode object.

    Auto encoding converison occurs if the plain string isn't encoded
    in UTF-8.

    Args:
        sub_str: The plain string intended to be converted to unicode
                 object
    Returns:
        sub_unicode: The converted unicode object

    '''
    encoding = chardet.detect(sub_str).get('encoding')
    if encoding:
        sub_unicode = unicode(sub_str, encoding, 'ignore')
    return sub_unicode

def to_cht(sub_unicode):
    '''Convert any Chinese unicode strings to Tradtional Chinese

    Args:
        sub_unicode: any Chinese unicode object
    Returns:
        sub_unicode: unicode object converted to Tradtional Chinese

    '''
    return __TONGWEN.conv_zh(sub_unicode, 'zht')

def to_chs(sub_unicode):
    '''Convert any Chinese unicode strings to Simplified Chinese

    Args:
        sub_unicode: any Chinese unicode object
    Returns:
        sub_unicode: unicode object converted to Simplified Chinese

    '''
    return __TONGWEN.conv_zh(sub_unicode, 'zhs')

def set_utf8_without_bom(sub_unicode):
    '''Convert a unicode object to plain string.

    Remove BOM header if exists

    Args:
        sub_unicode: any unicode object intended to be converted
                     to string
    Returns:
        sub_str: Plain string encoded in UTF-8 without BOM
    '''
    if sub_unicode.startswith(u'\ufeff'):
        sub_unicode = sub_unicode[3:]
    sub_str = sub_unicode.encode('utf-8')
    return sub_str

def reset_index(sub_unicode):
    '''Reset SRT subtitles index.

    The subtitle index increases incrementally from 1.

    Args:
        sub_unicode: unicode object containing SRT subtitles
    Returns:
        new_sub_unicode: Reordered unicode SRT object.

    '''
    subs = pysrt.from_string(sub_unicode)
    for i in range(1, len(subs) + 1):
        subs[i - 1].index = i

    new_sub = StringIO.StringIO()
    subs.write_into(new_sub)
    new_sub_unicode = new_sub.getvalue()
    new_sub.close()
    return new_sub_unicode
'''Few sanitizer functions to process subtitle text.
'''
import chardet
import codecs
from pyTongwen.conv import TongWenConv
import StringIO
import pysrt

__TONGWEN = TongWenConv()

def to_unicode(sub_str):
    '''Convert plain string to unicode object.

    Auto encoding converison occurs if the plain string isn't encoded
    in UTF-8.

    Args:
        sub_str: The plain string intended to be converted to unicode
                 object
    Returns:
        sub_unicode: The converted unicode object

    '''
    encoding = chardet.detect(sub_str).get('encoding')
    if encoding:
        sub_unicode = unicode(sub_str, encoding, 'ignore')
    return sub_unicode

def to_cht(sub_unicode):
    '''Convert any Chinese unicode strings to Tradtional Chinese

    Args:
        sub_unicode: any Chinese unicode object
    Returns:
        sub_unicode: unicode object converted to Tradtional Chinese

    '''
    return __TONGWEN.conv_zh(sub_unicode, 'zht')

def to_chs(sub_unicode):
    '''Convert any Chinese unicode strings to Simplified Chinese

    Args:
        sub_unicode: any Chinese unicode object
    Returns:
        sub_unicode: unicode object converted to Simplified Chinese

    '''
    return __TONGWEN.conv_zh(sub_unicode, 'zhs')

def set_utf8_without_bom(sub_unicode):
    '''Convert a unicode object to plain string.

    Remove BOM header if exists

    Args:
        sub_unicode: any unicode object intended to be converted
                     to string
    Returns:
        sub_str: Plain string encoded in UTF-8 without BOM
    '''
    sub_str = sub_unicode.encode('utf-8')
    if sub_str[:3] == codecs.BOM_UTF8:
        sub_str = sub_str[3:]
    return sub_str

def reset_index(sub_unicode):
    '''Reset SRT subtitles index.

    The subtitle index increases incrementally from 1.

    Args:
        sub_unicode: unicode object containing SRT subtitles
    Returns:
        new_sub_unicode: Reordered unicode SRT object.

    '''
    subs = pysrt.from_string(sub_unicode)
    for i in range(1, len(subs) + 1):
        subs[i - 1].index = i

    new_sub = StringIO.StringIO()
    subs.write_into(new_sub)
    new_sub_unicode = new_sub.getvalue()
    new_sub.close()
    return new_sub_unicode


name_seperator_re = '\.|\s|-|[|]|/'


def get_extra_filename(target_name, filename):
    name = target_name.lower()
    components = re.split(name_seperator_re, name)
    filename = filename.lower()
    extra_filename = filename

    def plus_extra_for_resolution(c, f):
        res_coms = ['2160p', '1080p', '720p', '480p']
        c = str(c).lower()
        f = str(f).lower()
        extra_per_level = 'resex'
        if c in res_coms:
            ex = ''
            expected_index = res_coms.index(c)
            for i in range(len(res_coms)):
                com = res_coms[i]
                if com not in f and i > expected_index:
                    ex += extra_per_level
            return ex
        return None

    plus_extra_name = ""
    for component in components:
        if component not in filename:
            if component == 'h264':
                component = 'h.264'
            elif component == 'h265':
                component = 'h.265'
            if component not in filename:
                p = plus_extra_for_resolution(component, filename)
                if p is None:
                    return None
                plus_extra_name += p
        extra_filename = extra_filename.replace(component, '', 1)
    extra_filename = re.sub(name_seperator_re, '', extra_filename)
    return extra_filename + plus_extra_name


def get_search_names(name):
    name = os.path.splitext(name)[0]
    search_names = [name]
    map_names = {'h264': 'h.264',
                 'h265': 'h.265',
                 'h.264': 'h264',
                 'h.256': 'h265',
                 '2160p': '',
                 '1080p': '',
                 '720p': ''}
    for ori in map_names.keys():
        new = map_names.get(ori)
        if ori in name.lower():
            search_names.append(name.lower().replace(ori, new))
    return search_names

