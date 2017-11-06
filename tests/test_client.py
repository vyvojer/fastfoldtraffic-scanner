import unittest
from client import *


class TestClient(unittest.TestCase):

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


class TestWindow(unittest.TestCase):

    def setUp(self):
        self.client = Client()
        self.client.connect_or_start()

    def test__eq__(self):
        tw1 = Window.from_control(self.client, self.client.app.top_window())
        tw2 = Window.from_control(self.client, self.client.app.top_window())

        self.assertEqual(tw1, tw2)


class TestList(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        client = Client()
        client.connect_or_start()
        cls.main_window =  Window(client, title_re='PokerStars Lobby')

    def test__init__(self):
        player_list = List(self.main_window, 'PokerStarsList2')

    def test_get_next(self):
        player_list = List(self.main_window, 'PokerStarsList2')
        first_value = player_list.reset()
        self.assertEqual(player_list.has_next, True)
        self.assertEqual(first_value, player_list.value)
        second_value = player_list.get_next()
        self.assertEqual(second_value, player_list.value)
        self.assertEqual(first_value, player_list.previous_value)

    def test_has_next(self):
        player_list = List(self.main_window, 'PokerStarsList2')
        player_list.control.type_keys('^{END}')
        player_list.get_value()
        self.assertEqual(player_list.has_next, True)
        player_list.get_next()
        self.assertEqual(player_list.has_next, False)

    def test_iterator(self):
        player_list = List(self.main_window, 'PokerStarsList2')
        for value in player_list:
            print(value)




