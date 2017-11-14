import unittest

from scanner.ocr import *

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
        self.assertEqual(first_value, player_list.clipboard)
        second_value = player_list.get_next()
        self.assertEqual(second_value, player_list.clipboard)
        self.assertEqual(first_value, player_list.previous_value)

    def test_has_next(self):
        player_list = ClientList(self.main_window, 'PokerStarsList2')
        player_list.control.type_keys('^{END}')
        player_list.get_row()
        self.assertEqual(player_list.has_next, True)
        player_list.get_next()
        self.assertEqual(player_list.has_next, False)




