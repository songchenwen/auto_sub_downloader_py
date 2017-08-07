#!/usr/bin/env python
#coding=utf-8
'''
This modules handles file decompression / extractions.
'''
import rarfile
import zipfile
from sanitizer import get_extra_filename
import os

class BaseCompressedFileHandler(object):
    '''Base Compressed File Handler.

    This exists since the interface of rarfile and zipfile
    are very similar. This might changes in time.

    Args:
        sub_buff: archieve binary data instance to be supplied.
        compression_class: modules to pass around.

    '''
    def __init__(self, sub_buff, compression_class):
        self.archieve_object = compression_class(sub_buff)

    def list_info(self):
        '''Return the file lists of the archieve.

        Returns:
            info_list: a list of dictionaries contains:
                       'size', 'name', 'info_obj'.

        '''
        info_list = []
        for i in self.archieve_object.infolist():
            info = {
                'size': i.file_size,
                'name': i.filename,
                'info_obj': i
            }
            info_list.append(info)
        return info_list

    def extract(self, filename):
        '''Extract subtitle, given its filename.

        Args:
            filename: the subtitle of filename to be extracted.
        Returns:
            raw_sub: the string data of the subtitle.

        '''
        raw_subfile = self.archieve_object.open(filename, 'r')
        raw_sub = raw_subfile.read()
        raw_subfile.close()
        return raw_sub



    def extract_bestguess(self, target_name):
        '''Extract subtitle by choosing the largest one.

        :param target_name: video file name without extension
        Returns:
            raw_sub: the string data of the subtitle.
        '''
        target_name = os.path.splitext(target_name)[0]
        info = self.list_info()
        high_score_extra_name = [u"简体", u"中文", u"英文", u'chs', u'chi', u'zh', u'zho', u'eng', u'en', u'cht', u'繁体']
        max_size = max([i['size'] for i in info])
        def score_for_info(i):
            name = str(i['name']).lower()
            print(name)
            basename = os.path.splitext(name)[0]
            ext = os.path.splitext(name)[1]
            score = 0.0
            if ext == '.ass':
                score += 8.0
            elif ext == '.srt':
                score += 0.0
            else:
                return -1
            extra_filename = get_extra_filename(target_name, basename)
            if extra_filename is None:
                return -1
            extra_filename.replace('&', '')
            for ind in range(len(high_score_extra_name)):
                n = high_score_extra_name[ind]
                if n in extra_filename:
                    score += (len(high_score_extra_name) - ind)
                    extra_filename.replace(n, '', 1)
            score += (float(100 - min(100, len(extra_filename))) / 100.0 * 10.0)
            score += (float(i['size']) / float(max_size) * 10.0)
            return score

        candidate = max(info, key=lambda x: score_for_info(x))
        if score_for_info(candidate) < 0:
            return None, None
        print('best uncompress guess %s for %s' % (candidate['name'], target_name))
        return candidate['name'], self.extract(candidate['name'])

class RARFileHandler(BaseCompressedFileHandler):
    '''RAR File Handler, subclass from BaseCompressedFileHandler.

    Args:
        sub_buff: archieve binary data instance to be supplied.
        compression_class: modules to pass around.

    '''
    def __init__(self, sub_buff):
        super(RARFileHandler, self).__init__(sub_buff, rarfile.RarFile)

class ZIPFileHandler(BaseCompressedFileHandler):
    '''ZIP File Handler, subclass from BaseCompressedFileHandler

    Args:
        sub_buff: archieve binary data instance to be supplied.
        compression_class: modules to pass around.

    '''
    def __init__(self, sub_buff):
        super(ZIPFileHandler, self).__init__(sub_buff, zipfile.ZipFile)
