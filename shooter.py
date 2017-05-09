import hashlib
import os
import requests
from requests.packages.urllib3 import disable_warnings
from log_utils import normalize_log_filename
from subtitle_utils import convert_ass_to_srt, check_subtitle_file, try_to_fix_subtitle_file
import sys
from args import need_srt

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
    filehash = calculate_checksum(filename)
    response = requests.post(
        "https://www.shooter.cn/api/subapi.php",
        verify=False,
        params= {
            'filehash': filehash,
            'pathinfo': os.path.realpath(filename),
            'format': 'json',
            'lang': "chi",
        },
    )
    if response.text == u'\xff':
        sys.stderr.write("Subtitle not found.\n")
        return None
    print('filehash %s' % filehash)
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
                subtitle_contents.add(_response.text)
                if check_contain_chinese(_response.text):
                    if len(subtitles) == 0:
                        _basename = "%s.chi" % (basename)
                    else:
                        _basename = "%s.chi.%s" % (basename, len(subtitles))

                    _filename = "%s.%s" % (_basename, ext)
                    fobj = open(_filename, 'w')
                    fobj.write(_response.text.encode("UTF8"))
                    fobj.close()
                    checked = check_subtitle_file(_filename)
                    if not checked:
                        checked = try_to_fix_subtitle_file(_filename)
                    if checked:
                        if str(ext).lower() == 'srt':
                            srt_count = srt_count + 1
                        subtitles.append(_filename)
                    else:
                        print('subtitle check failed %s' % normalize_log_filename(_filename))

    if len(subtitles) > 0:
        if srt_count == 0 and need_srt:
            srt_filename = convert_ass_to_srt(subtitles[0])
            if srt_filename is not None:
                subtitles.insert(0, srt_filename)
        print("%d subtitles for %s" % (len(subtitles), normalize_log_filename(filename)))
    else:
        print("no subtitles for %s" % normalize_log_filename(filename))

    return subtitles
