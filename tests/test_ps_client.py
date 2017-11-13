import unittest

from scan.osr import *

from scanner.client import *


class ClientTest(unittest.TestCase):

    def setUp(self):
        self.VALID_PATH = r'C:\Program Files (x86)\PokerStars\PokerStars.exe'
        self.INVALID_PATH = r'C:\Program Files (x86)\PokerStars\PokerStarss.exe'

    def test_connect_or_start(self):
        ps = Client(self.VALID_PATH)
        self.assertTrue(ps.connect_or_start())
        self.assertTrue(ps.app.is_process_running())

    def test_is_running(self):
        ps = Client()
        ps.connect_or_start()
        self.assertTrue(ps.is_running())


class WindowTest(unittest.TestCase):

    def setUp(self):
        self.client = Client()
        self.client.connect_or_start()

    def test__init(self):
        mw = ClientWindow(self.client, "PokerStars Lobby")
        tw = ClientWindow(self.client)
        self.assertEqual(mw.title, tw.title)

    def test__eq__(self):
        tw1 = ClientWindow.from_control(self.client, self.client.app.top_window())
        tw2 = ClientWindow.from_control(self.client, self.client.app.top_window())

        self.assertEqual(tw1, tw2)


class ListFieldTest(unittest.TestCase):

    def test_character(self):
        field = ListItem('name', 0, 0, None, value='2.90')
        self.assertEqual(field.parsed_value, '2.90')

    def test_int(self):
        field = ListItem('name', 0, 0, None, field_type=ListItem.INT, value='20')
        self.assertEqual(field.parsed_value, 20)

        field = ListItem('name', 0, 0, None, field_type=ListItem.INT, value='2.9s')
        self.assertEqual(field.parsed_value, 29)

        field = ListItem('name', 0, 0, None, field_type=ListItem.INT, value='s')
        self.assertEqual(field.parsed_value, 0)

    def test_float(self):
        field = ListItem('name', 0, 0, None, field_type=ListItem.FLOAT, value='2.90')
        self.assertEqual(field.parsed_value, 2.9)

        field = ListItem('name', 0, 0, None, field_type=ListItem.FLOAT, value='2.9s')
        self.assertEqual(field.parsed_value, 2.9)

        field = ListItem('name', 0, 0, None, field_type=ListItem.FLOAT, value='s')
        self.assertEqual(field.parsed_value, 0)

    def test_from_dict(self):
        field_dict = {
            'name': 'entries',
            'left_x': 190,
            'right_x': 220,
            'field_type': 'INT'
        }
        field = ListItem.from_dict(field_dict)
        self.assertEqual(field.name, 'entries')
        self.assertEqual(field.left_x, 190)
        self.assertEqual(field.right_x, 220)
        self.assertEqual(field.dataset_name, 'default')
        self.assertEqual(field.field_type, ListItem.INT)


class ListTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        client = Client()
        client.prepare()
        cls.main_window =  ClientWindow(client, title_re='PokerStars Lobby')

    def test__init__(self):
        player_list = ClientList(self.main_window, 'PokerStarsList2')

    def test_get_next(self):
        player_list = ClientList(self.main_window, 'PokerStarsList2')
        first_value = player_list.reset()
        self.assertEqual(player_list.has_next, True)
        self.assertEqual(first_value, player_list.value)
        second_value = player_list.get_next()
        self.assertEqual(second_value, player_list.value)
        self.assertEqual(first_value, player_list.previous_value)

    def test_has_next(self):
        player_list = ClientList(self.main_window, 'PokerStarsList2')
        player_list.control.type_keys('^{END}')
        player_list.get_value()
        self.assertEqual(player_list.has_next, True)
        player_list.get_next()
        self.assertEqual(player_list.has_next, False)



