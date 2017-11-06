import time
from pywinauto.application import Application

from zoomscanner import osr

STARS_PATH = r'C:\Program Files (x86)\PokerStars\PokerStars.exe'


class ListField:
    def __init__(self, name):
        self.name = name
        self.first_x = 0
        self.last_x = 0



class List:
    pass



class StarsList:
    def __init__(self, ps_list):
        self.list_ = ps_list
        self.header = None
        self.zones = None
        self.end_of_list = False
        self.variant = osr.TABLE_LIST
        self.current_record = None


class Scanner:
    def __init__(self, path=STARS_PATH):
        self.path = path
        self.app = None
        self.connect()
        self.main_window = self.app.window(title_re="PokerStars Lobby.*")
        self.table_list = StarsList(self.main_window['PokerStarsList'])
        self.table_list.header = self.main_window['PokerStarsHeaderClass']
        self.table_list.variant = osr.TABLE_LIST
        self.get_list_zones(self.table_list)

        self.player_list = StarsList(self.main_window['PokerStarsList2'])
        self.player_list.header = self.main_window['PokerStarsHeaderClass2']
        self.player_list.variant = osr.PLAYER_LIST
        self.get_list_zones(self.player_list)

    def connect(self):
        self.app = Application().connect(path=r'C:\Program Files (x86)\PokerStars\PokerStars.exe')

    @staticmethod
    def get_list_zones(ps_list: StarsList):
        ps_list.header.set_focus()
        time.sleep(1)
        header_image = ps_list.header.capture_as_image()
        ps_list.zones = osr.get_list_zones(header_image, ps_list=ps_list.variant)

    @staticmethod
    def reset_list(ps_list: StarsList):
        ps_list.list_.set_focus()
        ps_list.list_.type_keys('^{HOME}')
        ps_list.end_of_list = False

    def scan_list(self, ps_list: StarsList):
        self.reset_list(ps_list)
        self.recognize_fields(ps_list)
        while not ps_list.end_of_list:
            self.next_table(ps_list)
            if ps_list == self.table_list:
                self.scan_list(self.player_list)
            self.recognize_fields(ps_list)

    @staticmethod
    def next_table(ps_list: StarsList):
        ps_list.list_.set_focus()
        ps_list.list_.type_keys('{DOWN}')

    def recognize_fields(self, ps_list: StarsList):
        ps_list.list_.set_focus()
        list_image = ps_list.list_.capture_as_image()
        fields = osr.recognize_fields(list_image, ps_list.zones, ps_list=ps_list.variant)
        previous_record = ps_list.current_record
        ps_list.current_record = fields['name']

        if ps_list.current_record == previous_record:
            ps_list.end_of_list = True
        else:
            if ps_list == self.table_list:
                name = fields['name']
                stakes = fields['stakes'].replace(' ', '')
                game = fields['game']
                players = fields['plrs'].replace(' ', '')
                avg_pot = fields['avg_pot'].replace(' ', '')
                players_flop = fields['plrs_flop'].replace(' ', '')
                hands_hour = fields['hands_hour'].replace(' ', '')
                print(name, stakes, game, players, avg_pot, players_flop, hands_hour)
            else:
                name = fields['name']
                print(name)

    def main_loop(self):
        while (True):
            self.scan_list(self.table_list)
            osr.dump_symbols()
            time.sleep(10)
            print("----------")


if __name__ == '__main__':
    s = Scanner()
    s.main_loop()
