import unittest

import numpy as np
from PIL import Image
from scanner.ocr import _has_intersection, _unite_intersected, _get_united, _distinguish_flag, _find_flag
from scanner.ocr import ImageRecord, recognize_row, recognize_characters, recognize_flag

from scanner.client import *

from flags import rus_array


class TestIntersection(unittest.TestCase):
    def setUp(self):
        self.bound_rects = [(3, 7, 8, 10),
                            (13, 10, 1, 7),
                            (13, 7, 1, 1),
                            (16, 10, 6, 7),
                            (23, 8, 3, 9),
                            (28, 10, 1, 7),
                            (28, 7, 1, 1),
                            (31, 10, 9, 7),
                            (42, 10, 7, 7)]

    def test_intersection(self):
        self.assertFalse(_has_intersection(self.bound_rects[0], self.bound_rects[1]))
        self.assertTrue(_has_intersection(self.bound_rects[1], self.bound_rects[2]))
        self.assertFalse(_has_intersection(self.bound_rects[2], self.bound_rects[3]))
        self.assertFalse(_has_intersection(self.bound_rects[3], self.bound_rects[4]))
        self.assertFalse(_has_intersection(self.bound_rects[4], self.bound_rects[5]))
        self.assertTrue(_has_intersection(self.bound_rects[5], self.bound_rects[6]))
        self.assertFalse(_has_intersection(self.bound_rects[6], self.bound_rects[7]))
        self.assertFalse(_has_intersection(self.bound_rects[7], self.bound_rects[8]))

    def test_intesection_touched(self):
        rect = (58, 10, 7, 7)
        next_rect = (65, 10, 7, 10)
        self.assertFalse(_has_intersection(rect, next_rect))

    def test_unite_intersected(self):
        rect = self.bound_rects[1]
        next_rect = self.bound_rects[2]
        united = (13, 7, 1, 10)
        self.assertEqual(_unite_intersected(rect, next_rect), united)

    def test_get_united_Diotima(self):
        united = [(3, 7, 8, 10),
                  (13, 7, 1, 10),
                  (16, 10, 6, 7),
                  (23, 8, 3, 9),
                  (28, 7, 1, 10),
                  (31, 10, 9, 7),
                  (42, 10, 7, 7)]
        self.assertEqual(_get_united(self.bound_rects), united)

    def test_get_united_Devanssay(self):
        intersected = [(3, 7, 8, 10),
                       (13, 10, 6, 7),
                       (20, 10, 7, 7),
                       (28, 10, 7, 7),
                       (36, 10, 6, 7),
                       (44, 10, 5, 7),
                       (51, 10, 5, 7),
                       (58, 10, 7, 7),
                       (65, 10, 7, 10)]
        self.assertEqual(_get_united(intersected), intersected)


class SymbolsDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.img_of_2 = np.array([[0, 255, 255, 255, 255, 0],
                                 [255, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 255, 0],
                                 [0, 0, 0, 255, 0, 0],
                                 [0, 0, 255, 0, 0, 0],
                                 [0, 255, 0, 0, 0, 0],
                                 [255, 0, 0, 0, 0, 0],
                                 [255, 255, 255, 255, 255, 255]], dtype=np.uint8)

        cls.img_of_3 = np.array([[0, 255, 255, 255, 255, 0],
                                 [255, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 0, 255],
                                 [0, 0, 255, 255, 255, 0],
                                 [0, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [0, 255, 255, 255, 255, 0]], dtype=np.uint8)

    def test_save_load(self):
        sd = ImageLibrary('symbols_test.dat')
        sd.records = {'pu': 'tu'}
        sd.save_library()
        sd2 = ImageLibrary('symbols_test.dat')
        sd2.load_library()
        self.assertEqual(sd2.records['pu'], 'tu')

    def test_recognize_symbol(self):
        dataset = ImageLibrary(records={(10, 6): [ImageRecord(self.img_of_2, '2')]})
        _, symbol_record = dataset.get_image_record(self.img_of_2)
        self.assertEqual(symbol_record.text, '2')

    def test__iter_(self):
        dataset = ImageLibrary()
        dataset.get_image_record(self.img_of_2)
        dataset.get_image_record(self.img_of_3)
        symbols = [symbol.image for symbol in dataset]
        self.assertEqual(len(symbols), 2)
        self.assertIn(self.img_of_2, symbols)
        self.assertIn(self.img_of_2, symbols)


class TestParsers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.players_img_1 = pil_to_opencv(Image.open('osr_data/players_1.png'))
        cls.players_img_2 = pil_to_opencv(Image.open('osr_data/players_2.png'))
        cls.players_img_3 = pil_to_opencv(Image.open('osr_data/players_3.png'))
        cls.players_img_4 = pil_to_opencv(Image.open('osr_data/players_4.png'))
        cls.players_list_empty = pil_to_opencv(Image.open('osr_data/players_empty_list.png'))
        cls.row_img_1 = pil_to_opencv(Image.open('osr_data/row_1.png'))
        cls.row_img_2 = pil_to_opencv(Image.open('osr_data/row_2.png'))
        cls.row_img_3 = pil_to_opencv(Image.open('osr_data/row_3.png'))
        cls.row_img_4 = pil_to_opencv(Image.open('osr_data/row_4.png'))
        cls.img_of_2 = np.array([[0, 255, 255, 255, 255, 0],
                                 [255, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 255, 0],
                                 [0, 0, 0, 255, 0, 0],
                                 [0, 0, 255, 0, 0, 0],
                                 [0, 255, 0, 0, 0, 0],
                                 [255, 0, 0, 0, 0, 0],
                                 [255, 255, 255, 255, 255, 255]], dtype=np.uint8)

        cls.img_of_3 = np.array([[0, 255, 255, 255, 255, 0],
                                 [255, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 0, 255],
                                 [0, 0, 255, 255, 255, 0],
                                 [0, 0, 0, 0, 0, 255],
                                 [0, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [255, 0, 0, 0, 0, 255],
                                 [0, 255, 255, 255, 255, 0]], dtype=np.uint8)

    def test_find_row(self):
        zone = (170, 171)
        self.assertTrue(np.array_equal(recognize_row(self.players_img_1, zone=zone), self.row_img_1))
        self.assertTrue(np.array_equal(recognize_row(self.players_img_2, zone=zone), self.row_img_2))
        self.assertTrue(np.array_equal(recognize_row(self.players_img_3, zone=zone), self.row_img_3))
        self.assertTrue(np.array_equal(recognize_row(self.players_img_4, zone=zone), self.row_img_4))
        with self.assertRaises(ValueError) as raised:
            recognize_row(self.players_list_empty, zone=zone)
        self.assertEqual(raised.exception.args[0], "Can't recognize row")

    def test_recognize_text_entry(self):
        library = ImageLibrary(records={(10, 6): [
            ImageRecord(self.img_of_2, '2'),
            ImageRecord(self.img_of_3, '3'),
        ]
        })
        zone = (190, 220)
        text = recognize_characters(self.row_img_1, zone=zone, library=library)
        self.assertEqual(text, '2')

        zone = (190, 220)
        text = recognize_characters(self.row_img_2, zone=zone, library=library)
        self.assertEqual(text, '3')

    def test__find_flag(self):
        library = ImageLibrary(records={(16, 22, 3): [ImageRecord(rus_array,'rus')]})
        flag_image = _distinguish_flag(self.row_img_1[:, 140:170])
        was_created, image_record = _find_flag(flag_image, library)
        self.assertEqual(was_created, False)
        self.assertEqual(image_record.text, 'rus')

        # Brazil
        flag_image = _distinguish_flag(self.row_img_2[:, 140:170])
        was_created, image_record = _find_flag(flag_image, library)
        self.assertEqual(was_created, True)
        self.assertEqual(image_record.text, None)

        # Another brazil
        flag_image = _distinguish_flag(self.row_img_3[:, 140:170])
        was_created, image_record = _find_flag(flag_image, library)
        self.assertEqual(was_created, False)
        self.assertEqual(image_record.text, None)

    def test_recognize_flag(self):
        library = ImageLibrary(records={(16, 22, 3): [ImageRecord(rus_array,'rus')]})
        zone = (140, 170)
        country = recognize_flag(self.row_img_1,zone=zone, library=library)
        self.assertEqual(country, 'rus')
