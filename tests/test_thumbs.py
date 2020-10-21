from context import thumbnailflow

import unittest
import tempfile
import os
import json
from PIL import Image
import time


class ThumbsTC(unittest.TestCase):

    def setUp(self):
        self.setup_time = time.time()
        self.dir = tempfile.TemporaryDirectory()
        self.thumbfile_path = os.path.join(
                                    self.dir.name,
                                    thumbnailflow.thumbnails.DEFAULT_FILENAME)
        # create some content
        self.example_dir = os.path.join(self.dir.name, 'exampledir')
        os.mkdir(self.example_dir)
        self.example_txt = os.path.join(self.dir.name, 'example.txt')
        with open(self.example_txt, 'w') as fp:
            fp.write('example')
        self.example_png = os.path.join(self.dir.name, 'example.png')
        png = Image.new('RGB', (100,100))
        png.save(self.example_png, 'PNG')

    def tearDown(self):
        self.dir.cleanup()

    def test_generate_dir(self):
        t_object = thumbnailflow.thumbnails.Thumbnail(root=self.dir.name, name='exampledir')
        py_dict = t_object.getDict()
        self.assertEqual(py_dict['name'], 'exampledir')
        self.assertEqual(py_dict['type'], 'dir')

    def test_generate_txt(self):
        t_object = thumbnailflow.thumbnails.Thumbnail(root=self.dir.name, name='example.txt')
        py_dict = t_object.getDict()
        self.assertEqual(py_dict['name'], 'example.txt')
        self.assertEqual(py_dict['type'], 'txt')
        self.assertLess(py_dict['touched'], time.time(), 'Touched in future')
        self.assertLess(self.setup_time, time.time(), 'Setup in future')

    def test_generate_png(self):
        t_object = thumbnailflow.thumbnails.Thumbnail(root=self.dir.name, name='example.png')
        py_dict = t_object.getDict()
        self.assertEqual(py_dict['name'], 'example.png')
        self.assertEqual(py_dict['type'], 'png')
        self.assertGreater(len(py_dict.get('data_url', '')), 1)
        self.assertNotIn('\n', py_dict['data_url'], 'There is a newline')

    def test_get_dirs(self):
        names = []
        for thumb in thumbnailflow.thumbnails.generateDirThumbs(self.dir.name):
            py_dict = json.loads(thumb)
            names.append(py_dict['name'])
        self.assertEqual(len(names), 1)
        self.assertIn('exampledir', names)

    def test_get_files_without_preserve(self):
        names = []
        for thumb in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name):
            py_dict = json.loads(thumb)
            names.append(py_dict['name'])
        self.assertEqual(len(names), 2)
        self.assertIn('example.txt', names)
        self.assertIn('example.png', names)
        if os.path.isfile(self.thumbfile_path):
            self.assertTrue(False, 'Preserved thumbs')

    def test_get_files_with_preserve(self):
        names = []
        for thumb in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name, True):
            py_dict = json.loads(thumb)
            names.append(py_dict['name'])
        self.assertEqual(len(names), 2)
        self.assertIn('example.txt', names)
        self.assertIn('example.png', names)
        if not(os.path.isfile(self.thumbfile_path)):
            self.assertTrue(False, 'No thumbs file generated')
        with open(self.thumbfile_path,'r') as fp:
            try:
                json.load(fp)
            except Exception as err:
                lines = ''.join(fp.readlines())
                self.assertTrue(False, 'json error {} file is {}'.format(err, lines))


    def test_usage_of_perserved(self):
        thumbs = [t for t in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name, True)]
        first_creation = os.path.getmtime(self.thumbfile_path)
        #time.sleep(0.1)
        thumbs = [t for t in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name, True)]
        if not(os.path.isfile(self.thumbfile_path)):
            self.assertTrue(False, 'No thumbs file generated')
        thumbs_created = os.path.getmtime(self.thumbfile_path)
        self.assertEqual(thumbs_created,
                        first_creation,
                        'Created too often')
        # let some time pass
        time.sleep(0.1)
        # set the timestamp
        os.utime(self.example_png, None)
        thumbs = {}
        for thumb in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name, True):
            py_dict = json.loads(thumb)
            thumbs[py_dict['name']] = py_dict
        png_touched = max(os.path.getmtime(self.thumbfile_path),
                          os.path.getctime(self.thumbfile_path))
        self.assertGreater(png_touched,
                           first_creation,
                           'Touch did not work')
        self.assertGreater(thumbs['example.png']['touched'],
                           first_creation,
                           'Not updated')

        self.assertEqual(self.count_thumbfiles(), 1, 'Temp file not deleted')

    def test_remove_tempfile(self):
        thumbs = [t for t in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name, True)]
        time.sleep(0.1)
        # set the timestamp
        os.utime(self.example_png, None)
        os.utime(self.example_txt, None)
        for t in thumbnailflow.thumbnails.generateFileThumbs(self.dir.name, True):
            break
        self.assertEqual(self.count_thumbfiles(), 1, 'Temp file not deleted')

    def count_thumbfiles(self):
        thumb_files_found = 0
        for root, dirs, files in os.walk(self.dir.name):
            for f in files:
                if f.startswith(thumbnailflow.thumbnails.DEFAULT_FILENAME):
                    thumb_files_found += 1
            break
        return thumb_files_found
