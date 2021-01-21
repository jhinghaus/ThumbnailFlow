#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Jens Hinghaus <jhinghaus@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

THUMB_SIZE = 64, 64
IMAGE_TYPES = ['jpg','jpeg','bmp','gif','png']
DEFAULT_FILENAME = '.thumbs.json'

import os
import os.path
from PIL import Image
from io import BytesIO
import base64
import json
import uuid
import thumbnailflow.devnull


def generate_dir_thumbs(folder):
    '''
    Generator returning thumbnails for folders in the given folder in json.
    No preserve flag implemented so far.
    Preview of contained files could be implemented later.
    '''
    if not(os.path.isdir(folder)):
        return
    dir_thumbs = make_dir_thumbs(folder=folder)
    concat = '[\n'
    for thumbnail in dir_thumbs:
        thumb_dict = thumbnail.as_dict()
        thumb_json = concat + json.dumps(thumb_dict)
        yield thumb_json
        concat = ',\n'
    yield ']'

def generate_file_thumbs(folder, preserve=False):
    '''
    Generator returning thumbsnails for files in the given folder in json.
    Checks for an existing file with generated thumbnails.
    '''

    if not(os.path.isdir(folder)):
        return
    # check for a thumbnail-file
    old_thumbs_file = os.path.join(folder,DEFAULT_FILENAME)

    file_thumbs = make_file_thumbs(folder=folder)
    known_iterator = generate_known_thumbs(old_thumbs_file)
    # start the iterator before we open the file to write
    current_known = next(known_iterator)
    if preserve:
        new_thumbs_file = old_thumbs_file + str(uuid.uuid4())
        fp = open(new_thumbs_file,'w', encoding='utf-8')
    else:
        fp = thumbnailflow.devnull.DevNull()
    dirty = False

    try:
        concat = '[\n'
        for thumbnail in file_thumbs:
            if ((current_known['name'] == thumbnail.name) and
                (current_known['touched'] == thumbnail.touched)):
                thumb_dict = current_known
                current_known = next(known_iterator)
            else:
                thumb_dict = thumbnail.as_dict()
                dirty = True
            thumb_json = concat + json.dumps(thumb_dict)
            fp.write(thumb_json)
            yield thumb_json
            concat = ',\n'
    except GeneratorExit:
        # the new file can't be complete: Do not write.
        dirty = False
    if preserve:
        if dirty:
            fp.seek(fp.tell() - 2, os.SEEK_SET)
            fp.write(']')
            fp.close()
            os.replace(new_thumbs_file, old_thumbs_file)
        else:
            fp.seek(0)
            fp.truncate()
            fp.close()
            os.remove(new_thumbs_file)
    yield ']'

def make_file_thumbs(folder):
    '''  Returns a list of Thumbnail objects
    for the files in the given folder.
    The files are sorted by date desc '''

    file_thumbs = []
    for root, dirs, files in os.walk(folder):
        filepaths = []
        for filename in files:
            if filename == DEFAULT_FILENAME:
                continue
            f = Thumbnail(root=root, name=filename)
            file_thumbs.append(f)
        break # only this folder
    return sorted(file_thumbs,
                  key=Thumbnail.key_touched,
                  reverse=True)

def make_dir_thumbs(folder):
    '''  Returns a list of Thumbnail objects
    for the folders in the given folder.'''

    dir_thumbs = []
    for root, dirs, files in os.walk(folder):
        filepaths = []
        for dirname in dirs:
            dir_thumbs.append(Thumbnail(root=root, name=dirname))
        break # only this folder
    return dir_thumbs

def generate_known_thumbs(path):
    ''' Generate thumbnail dictionaries from the given file
    return a dummy when exhausted'''

    known_thumbs = []
    if os.path.isfile(path):
        with open(path,'r') as fp:
            for line in fp:
                if not(line in ('[\n', ']')):
                    yield json.loads(line[:-2])

    yield {'name':'', 'touched':0}

class Thumbnail(object):
    '''
    Thumbnail of one file.
    Image files will have a data_url.
    The data_url is created only when needed.
    '''

    @staticmethod
    def key_touched(tf):
        return tf.touched

    def __init__(self, root, name):
        self.name = name
        self.path = os.path.abspath(os.path.join(root, name))
        self.touched = max(os.path.getmtime(self.path),
                      os.path.getctime(self.path))
        if os.path.isdir(self.path):
            self.type ='dir'
        else:
            components = os.path.splitext(self.path)
            self.type = components[1].lower().lstrip('.')

    def data_url(self):

        if self.type in IMAGE_TYPES:
            # read the image
            image = Image.open(self.path)
            image.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
            # write the thumbnail to a buffer
            output = BytesIO()
            image.save(output, format='JPEG')
            image_data = output.getvalue()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return 'data:image/jpeg;base64,' + base64_string
        else:
            return ''

    def as_dict(self):

        return {'name': self.name,
                'type': self.type,
                'touched': self.touched,
                'data_url': self.data_url()}
