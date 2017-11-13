import unittest

import numpy as np
from PIL import Image

from scanner.client import ListRow, ListItem, float_parser, int_parser
from scanner.ocr import find_row, pil_to_opencv


class ListRowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.players_img_1 = Image.open('osr_data/players_1.png')
        cls.players_img_2 = Image.open('osr_data/players_2.png')
        cls.players_img_3 = Image.open('osr_data/players_3.png')
        cls.players_img_4 = Image.open('osr_data/players_4.png')
        cls.players_list_empty = Image.open('osr_data/players_empty_list.png')
        cls.row_img_1 = Image.open('osr_data/row_1.png')
        cls.row_img_2 = Image.open('osr_data/row_2.png')
        cls.row_img_3 = Image.open('osr_data/row_3.png')
        cls.row_img_4 = Image.open('osr_data/row_4.png')

    def test_find_row(self):
        list_row = ListRow(find_func=find_row, zone=(170, 171))
        list_row.find(pil_to_opencv(self.players_img_1))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_1)))

        list_row.find(pil_to_opencv(self.players_img_2))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_2)))

        list_row.find(pil_to_opencv(self.players_img_3))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_3)))

        list_row.find(pil_to_opencv(self.players_img_4))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_4)))

        list_row.find(pil_to_opencv(self.players_list_empty))
        self.assertEqual(list_row.image, None)


class ListFieldTest(unittest.TestCase):

    def test_from_dict(self):
        field_dict = {
            'name': 'entries',
            'x1': 190,
            'x2': 220,
        }

        field = ListItem.from_dict(field_dict)
        self.assertEqual(field.name, 'entries')
        self.assertEqual(field.x1, 190)
        self.assertEqual(field.x2, 220)
        self.assertEqual(field.dataset_name, None)


class ClientListTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_players_img_1 = Image.open('osr_data/players_1.png')
        cls.test_players_img_2 = Image.open('osr_data/players_2.png')
        cls.test_players_img_3 = Image.open('osr_data/players_3.png')
        cls.test_players_img_4 = Image.open('osr_data/players_4.png')


class ParsersTest(unittest.TestCase):

    def test_int_parser(self):
        self.assertEqual(int_parser('20'), 20)

        self.assertEqual(int_parser('2.9s'), 29)

        self.assertEqual(int_parser('s'), None)

    def test_float(self):
        self.assertEqual(float_parser('2.90'), 2.9)

        self.assertEqual(float_parser('2.9s'), 2.9)

        self.assertEqual(float_parser('s'), None)
