import json
import logging.config
import os.path
import sys
import argparse
import time

from scanner import settings
from scanner.client import *

logging.config.dictConfig(settings.logging_config)
logging.setLoggerClass(ImageLogger)
log = logging.getLogger(__name__)


class Scanner:
    def __init__(self, only_once=False, save_characters=False, save_flags=False, only_tables=False):
        self.client = Client()
        self.client.prepare()
        self.to_file = True
        self.only_once=only_once
        self.library_for_saving = []
        if save_characters:
            self.library_for_saving.append('pokerstars_characters')
        if save_flags:
            self.library_for_saving.append('pokerstars_flags')
        self.only_tables=only_tables

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
            log.info("Scanning table {}. Plrs: {} Avg Pot: ${} Plrs/Flop: {}".format(table['name'],
                                                                                         table['player_count'],
                                                                                         table['average_pot'],
                                                                                         table['players_per_flop'],
                                                                                         ))
            if not self.only_tables and table['player_count'] > 0:
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
                self.client.save_datasets(include=self.library_for_saving)
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
    parser = argparse.ArgumentParser(description='Pokerstars scanner')
    parser.add_argument('--once', '-o', action='store_true', help='scan only once', default=False)
    parser.add_argument('-sc', action='store_true', help='save character library', default=False)
    parser.add_argument('-sf', action='store_true', help='save flag library', default=False)
    parser.add_argument('--tables', '-t', action='store_true', help='scan only tables', default=False)
    parser.add_argument('--verbose', action='store_true', help='verbose info', default=False)
    parser.add_argument('--debug', action='store_true', help='debug info', default=False)
    args = parser.parse_args()
    print(args.tables)
    if args.verbose:
        log.setLevel(logging.INFO)
    if args.debug:
        log.setLevel(logging.DEBUG)
    s = Scanner(only_once=args.once, save_characters=args.sc, save_flags=args.sf, only_tables=args.tables)
    s.main_loop()
