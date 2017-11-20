import json
import logging.config
import os.path
import sys
import time

from scanner import settings
from scanner.client import *

logging.config.dictConfig(settings.logging_config)
logging.setLoggerClass(ImageLogger)
log = logging.getLogger(__name__)


class Scanner:
    def __init__(self):
        self.client = Client()
        self.client.prepare()
        self.to_file = True

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
        tables = []
        scan = {}
        log.info("Start scanning tables...")
        for table in self.client.table_list:
            log.info("Scanning table {}. Plrs: {} Avg Pot: ${} Plrs/Flop: {} H/hr: {}".format(table['name'],
                                                                                         table['player_count'],
                                                                                         table['average_pot'],
                                                                                         table['players_per_flop'],
                                                                                         table['hands_per_hour'],
                                                                                         ))
            if table['player_count'] > 0:
                unique_players_count, entries_count, players = self.scan_players()
                if not self._is_players_count_almost_equal(table['player_count'], entries_count):
                    unique_players_count, entries_count, players = self.scan_players()
                table['unique_player_count'] = unique_players_count
                table['entry_count'] = entries_count
                table['players'] = players
            else:
                table['unique_player_count'] = 0
                table['entry_count'] = 0
                table['players'] = []
            log.info("Table {} was scaned. Plrs: {} Entrs: {}".format(table['name'],
                                                                      table['unique_player_count'],
                                                                      table['entry_count'],
                                                                      ))
            tables.append(table)
        log.info("All tables was scanned")
        scan['room'] = settings.pokerstars['room']
        scan['tables'] = tables
        self._handle_scan(scan)

    def _handle_scan(self, scan):
        if self.to_file:
            file_name = 'dump-{}.json'.format(time.time())
            fine_name = 'dump.json'
            with open(os.path.join(settings.json_dir, file_name), 'w') as file:
                json.dump(scan, file, indent=4)
        else:
            print(json.dumps(scan, indent=4))

    def main_loop(self):
        try:
            while True:
                try:
                    self.client.prepare()
                    self.scan_tables()
                except Exception:
                    log.error("Exception during scan", exc_info=True)
                self.client.save_datasets()
                time.sleep(30)
        except KeyboardInterrupt:
            print("You pressed Ctrl+C")
            sys.exit(0)

    @staticmethod
    def _is_players_count_almost_equal(players, entries):
        if abs(players - entries) < 10:
            return True
        else:
            return False


if __name__ == '__main__':
    s = Scanner()
    s.main_loop()
