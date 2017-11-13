import unittest

import numpy as np
from PIL import Image

from scanner.client import ListRow, pil_to_opencv
from scanner.osr import find_row


class ListRowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.players_list_img_1 = Image.open('osr_data/test_players_1.png')
        cls.players_list_img_2 = Image.open('osr_data/test_players_2.png')
        cls.players_list_img_3 = Image.open('osr_data/test_players_3.png')
        cls.players_list_img_4 = Image.open('osr_data/test_players_4.png')
        cls.players_list_empty = Image.open('osr_data/test_players_empty_list.png')
        cls.row_img_1 = Image.open('osr_data/row_1.png')
        cls.row_img_2 = Image.open('osr_data/row_2.png')
        cls.row_img_3 = Image.open('osr_data/row_3.png')
        cls.row_img_4 = Image.open('osr_data/row_4.png')

    def test_find_row(self):
        list_row = ListRow(find_func=find_row, func_kwargs={'zone':(170,171)})
        list_row.find(pil_to_opencv(self.players_list_img_1))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_1)))

        list_row.find(pil_to_opencv(self.players_list_img_2))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_2)))

        list_row.find(pil_to_opencv(self.players_list_img_3))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_3)))

        list_row.find(pil_to_opencv(self.players_list_img_4))
        self.assertTrue(np.array_equal(list_row.image, pil_to_opencv(self.row_img_4)))

        list_row.find(pil_to_opencv(self.players_list_empty))
        self.assertEqual(list_row.image, None)


class ClientListTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_players_img_1 = Image.open('osr_data/test_players_1.png')
        cls.test_players_img_2 = Image.open('osr_data/test_players_2.png')
        cls.test_players_img_3 = Image.open('osr_data/test_players_3.png')
        cls.test_players_img_4 = Image.open('osr_data/test_players_4.png')


