import time
from pywinauto.application import Application

from zoomscanner import osr

STARS_PATH = r'C:\Program Files (x86)\PokerStars\PokerStars.exe'


class Scanner:

    def __init__(self, path=STARS_PATH):
        self.path = path
        self.app = None
        self.connect()
        self.main_window = self.app.window(title_re="PokerStars Lobby.*")
        self.table_list = self.main_window['PokerStarsList']
        self.table_list_header = self.main_window['PokerStarsHeaderClass']
        self.table_list_zones = None
        self.count_headers_zones()
        self.reset_table_list()
        self.player_list = None
        self.table = None
        self.end_of_tables = False

    def connect(self):
        self.app = Application().connect(path=r'C:\Program Files (x86)\PokerStars\PokerStars.exe')

    def count_headers_zones(self):
        self.table_list_header.set_focus()
        header_image = self.table_list_header.capture_as_image()
        self.table_list_zones = osr.get_list_zones(header_image)

    def reset_table_list(self):
        self.table_list.set_focus()
        self.table_list.type_keys('^{HOME}')
        self.end_of_tables = False

    def scan_table_list(self):
        self.reset_table_list()
        self.recognize_table_fields()
        while not self.end_of_tables:
            self.next_table()
            self.recognize_table_fields()

    def next_table(self):
        self.table_list.set_focus()
        self.table_list.type_keys('{DOWN}')

    def recognize_table_fields(self):
        self.table_list.set_focus()
        table_list_image = self.table_list.capture_as_image()
        fields = osr.recognize_fields(table_list_image, self.table_list_zones)
        previous_table = self.table
        self.table = fields['name']
        print(self.table)
        if self.table == previous_table:
            self.end_of_tables = True

    def main_loop(self):
        while (True):
            self.scan_table_list()
            osr.dump_symbols()
            time.sleep(10)
            print("----------")



if __name__ == '__main__':
    s = Scanner()
    s.scan_table_list()
    s.main_loop()

