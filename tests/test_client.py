import unittest

import numpy as np
from PIL import Image

from scanner.client import *
from scanner.ocr import *

players_img_1 = pil_to_opencv(Image.open('osr_data/players_1.png'))
players_img_2 = pil_to_opencv(Image.open('osr_data/players_2.png'))
players_img_3 = pil_to_opencv(Image.open('osr_data/players_3.png'))
players_img_4 = pil_to_opencv(Image.open('osr_data/players_4.png'))
players_list_empty = pil_to_opencv(Image.open('osr_data/players_empty_list.png'))
row_img_1 = pil_to_opencv(Image.open('osr_data/row_1.png'))
row_img_2 = pil_to_opencv(Image.open('osr_data/row_2.png'))
row_img_3 = pil_to_opencv(Image.open('osr_data/row_3.png'))
row_img_4 = pil_to_opencv(Image.open('osr_data/row_4.png'))
img_of_2 = np.array([[0, 255, 255, 255, 255, 0],
                     [255, 0, 0, 0, 0, 255],
                     [255, 0, 0, 0, 0, 255],
                     [0, 0, 0, 0, 0, 255],
                     [0, 0, 0, 0, 255, 0],
                     [0, 0, 0, 255, 0, 0],
                     [0, 0, 255, 0, 0, 0],
                     [0, 255, 0, 0, 0, 0],
                     [255, 0, 0, 0, 0, 0],
                     [255, 255, 255, 255, 255, 255]], dtype=np.uint8)
img_of_3 = np.array([[0, 255, 255, 255, 255, 0],
                     [255, 0, 0, 0, 0, 255],
                     [255, 0, 0, 0, 0, 255],
                     [0, 0, 0, 0, 0, 255],
                     [0, 0, 255, 255, 255, 0],
                     [0, 0, 0, 0, 0, 255],
                     [0, 0, 0, 0, 0, 255],
                     [255, 0, 0, 0, 0, 255],
                     [255, 0, 0, 0, 0, 255],
                     [0, 255, 255, 255, 255, 0]], dtype=np.uint8)


class ListRowTest(unittest.TestCase):
    def test_find_row(self):
        list_row = ListRow(recognizer=recognize_row, zone=(170, 171))
        list_row.recognize(players_img_1)
        self.assertTrue(np.array_equal(list_row.image, row_img_1))

        list_row.recognize(players_img_2)
        self.assertTrue(np.array_equal(list_row.image, row_img_2))

        list_row.recognize(players_img_3)
        self.assertTrue(np.array_equal(list_row.image, row_img_3))

        list_row.recognize(players_img_4)
        self.assertTrue(np.array_equal(list_row.image, row_img_4))

        with self.assertRaises(ValueError):
            list_row.recognize(players_list_empty)
        self.assertEqual(list_row.image, None)


class ListItemTest(unittest.TestCase):
    def test_from_dict(self):
        field_dict = {
            'name': 'entries',
            'zone': (190, 220),
            'recognizer': 'recognize_characters',
            'parser': 'int_parser',
        }

        field = ListItem.from_dict(field_dict)
        self.assertEqual(field.name, 'entries')
        self.assertEqual(field.zone, (190, 220))
        self.assertEqual(field.recognizer, recognize_characters)
        self.assertEqual(field.parser, int_parser)

    def test_recognize_field(self):
        library = ImageLibrary(records={(10, 6): [
            ImageRecord(img_of_2, '2'),
            ImageRecord(img_of_3, '3'),
        ]
        })
        list_item = ListItem('entry',
                             recognizer=recognize_characters,
                             parser=int_parser,
                             zone=(190, 220),
                             library=library)
        list_item.recognize(row_image=row_img_1)
        self.assertEqual(list_item.value, 2)
        list_item.recognize(row_image=row_img_2)
        self.assertEqual(list_item.value, 3)


class ClientListTest(unittest.TestCase):
    pass


class ParsersTest(unittest.TestCase):
    def test_int_parser(self):
        self.assertEqual(int_parser('20'), 20)

        self.assertEqual(int_parser('2.9s'), 29)

        self.assertEqual(int_parser('s'), None)

    def test_float(self):
        self.assertEqual(float_parser('2.90'), 2.9)

        self.assertEqual(float_parser('2.9s'), 2.9)

        self.assertEqual(float_parser('s'), None)
