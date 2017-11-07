import unittest
from PIL import Image
import numpy as np

from zoomscanner.osr import SymbolsDataset, SymbolRecord
from zoomscanner.osr import Osr
from client import *


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
        self.assertFalse(Osr._has_intersection(self.bound_rects[0], self.bound_rects[1]))
        self.assertTrue(Osr._has_intersection(self.bound_rects[1], self.bound_rects[2]))
        self.assertFalse(Osr._has_intersection(self.bound_rects[2], self.bound_rects[3]))
        self.assertFalse(Osr._has_intersection(self.bound_rects[3], self.bound_rects[4]))
        self.assertFalse(Osr._has_intersection(self.bound_rects[4], self.bound_rects[5]))
        self.assertTrue(Osr._has_intersection(self.bound_rects[5], self.bound_rects[6]))
        self.assertFalse(Osr._has_intersection(self.bound_rects[6], self.bound_rects[7]))
        self.assertFalse(Osr._has_intersection(self.bound_rects[7], self.bound_rects[8]))

    def test_intesection_touched(self):
        rect = (58, 10, 7, 7)
        next_rect = (65, 10, 7, 10)
        self.assertFalse(Osr._has_intersection(rect, next_rect))

    def test_unite_intersected(self):
        rect = self.bound_rects[1]
        next_rect = self.bound_rects[2]
        united = (13, 7, 1, 10)
        self.assertEqual(Osr._unite_intersected(rect, next_rect), united)

    def test_get_united_Diotima(self):
        united = [(3, 7, 8, 10),
                  (13, 7, 1, 10),
                  (16, 10, 6, 7),
                  (23, 8, 3, 9),
                  (28, 7, 1, 10),
                  (31, 10, 9, 7),
                  (42, 10, 7, 7)]
        self.assertEqual(Osr._get_united(self.bound_rects), united)

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
        self.assertEqual(Osr._get_united(intersected), intersected)


class SymbolsDatasetTest(unittest.TestCase):
    def test_save_load(self):
        sd = SymbolsDataset('symbols_test.dat')
        sd.symbols = {'pu': 'tu'}
        sd.save_dataset()
        sd2 = SymbolsDataset('symbols_test.dat')
        sd2.load_dataset()
        self.assertEqual(sd2.symbols['pu'], 'tu')


class OsrTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_players_img_1 = Image.open('osr_data/test_players_1.png')
        cls.test_players_img_2 = Image.open('osr_data/test_players_2.png')
        cls.test_players_img_3 = Image.open('osr_data/test_players_3.png')
        cls.test_players_img_4 = Image.open('osr_data/test_players_4.png')
        cls.test_players_img_empty_list = Image.open('osr_data/test_players_empty_list.png')
        cls.players_cursor = (170, 171)
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

    def test_players_cursor(self):
        osr = Osr(self.test_players_img_1, cursor=self.players_cursor, fields=[], dataset_dict={})
        top, bottom = osr._recognize_cursor()
        self.assertEqual(top, 0)
        self.assertEqual(bottom, 20)

        osr = Osr(self.test_players_img_2, cursor=self.players_cursor, fields=[], dataset_dict={})
        top, bottom = osr._recognize_cursor()
        self.assertEqual(top, 21)
        self.assertEqual(bottom, 41)

        osr = Osr(self.test_players_img_3, cursor=self.players_cursor, fields=[], dataset_dict={})
        top, bottom = osr._recognize_cursor()
        self.assertEqual(top, 42)
        self.assertEqual(bottom, 62)

        osr = Osr(self.test_players_img_4, cursor=self.players_cursor, fields=[], dataset_dict={})
        top, bottom = osr._recognize_cursor()
        self.assertEqual(top, 399)
        self.assertEqual(bottom, 419)

    def test_players_cursor_with_empty_list(self):
        osr = Osr(self.test_players_img_empty_list, cursor=self.players_cursor, fields=[], dataset_dict={})
        with self.assertRaises(ValueError) as raised:
            top, bottom = osr._recognize_cursor()
        self.assertEqual(raised.exception.args[0], "Can't recognize cursor")

    def test_recognize_text(self):
        dataset = SymbolsDataset(symbols={(10, 6): [SymbolRecord(self.img_of_2, '2')]})
        osr = Osr(self.test_players_img_1, cursor=self.players_cursor, fields=[], dataset_dict={})
        text = osr._recognize_text(osr.gray_image[0:20, 190:220], dataset)
        self.assertEqual(text, '2')

    def test_recognize_symbol(self):
        dataset = SymbolsDataset(symbols={(10, 6):[SymbolRecord(self.img_of_2, '2')]})
        osr = Osr(self.test_players_img_1, cursor=self.players_cursor, fields=[], dataset_dict={})
        symbol = osr._recognize_symbol(self.img_of_2, dataset)
        self.assertEqual(symbol, '2')

    def test_recognize_fields(self):
        dataset = SymbolsDataset(symbols={(10, 6): [SymbolRecord(self.img_of_2, '2')]})
        dataset_dict = {'default': dataset}
        entry_field = ListField('entries', 190, 220, dataset_name='default')
        osr = Osr(self.test_players_img_1, cursor=self.players_cursor, fields=[entry_field], dataset_dict=dataset_dict)
        osr.recognize_fields()
        self.assertEqual(entry_field.value, '2')

