import time
import logging
import logging.config

from zoomscanner.client import *
from zoomscanner import settings

logging.config.dictConfig(settings.logging_config)
log = logging.getLogger(__name__)


class Scanner:
    def __init__(self):
        self.client = Client()
        self.client.prepare()

    def scan_players(self):
        self.client.move_main_window()
        self.client.close_not_main_windows()
        players = []
        entries_count = 0
        unique_players_count = 0
        for player in self.client.player_list:
            unique_players_count += 1
            entries_count += int(player['entries'])
            players.append(player)
        return unique_players_count, entries_count, players

    def scan_tables(self):
        self.client.move_main_window()
        self.client.close_not_main_windows()
        for table in self.client.table_list:
            if table['players_count'] > 0:
                unique_players_count, entries_count, players = self.scan_players()
                if not self._is_players_count_almost_equal(table['players_count'], entries_count):
                    unique_players_count, entries_count, players = self.scan_players()
                table['unique_players_count'] = unique_players_count
                table['entries_count'] = entries_count
                table['players'] = players
            else:
                table['unique_players_count'] = 0
                table['entries_count'] = 0
                table['players'] = []
            print(table)


    def main_loop(self):
        while True:
            try:
                self.client.prepare()
                self.scan_tables()
            except Exception:
                log.error("Exception during scan", exc_info=True)
            time.sleep(30)



    @staticmethod
    def _is_players_count_almost_equal(players, entries):
        if abs(players - entries) < 10:
            return True
        else:
            return False




if __name__ == '__main__':
    s = Scanner()
    s.main_loop()
    s.client.save_datasets()

