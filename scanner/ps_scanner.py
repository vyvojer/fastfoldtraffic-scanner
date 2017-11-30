import datetime
import json
import logging.config
import os.path
import sys
from argparse import ArgumentParser
import time

import requests

from scanner import settings, ocr, client

logging.config.dictConfig(settings.logging_config)
logging.setLoggerClass(ocr.ImageLogger)
log = logging.getLogger("scanner.ps_scanner")


class Scanner:
    def __init__(self,
                 save_only=False,
                 library_dir=None,
                 only_once=False,
                 save_characters=False,
                 save_flags=False,
                 only_tables=False):
        self.save_only = save_only,
        if library_dir is None:
            self.library_dir = settings.package_dir
        else:
            self.library_dir = library_dir
        self.client = client.Client(library_dir=self.library_dir)
        self.client.prepare()
        self.to_file = True
        self.only_once = only_once
        self.library_for_saving = []
        if save_characters:
            self.library_for_saving.append('pokerstars_characters')
        if save_flags:
            self.library_for_saving.append('pokerstars_flags')
        self.only_tables = only_tables

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
        scan_result = {}
        log.debug("Start scanning tables...")
        for table in self.client.table_list:
            log.debug("Scanning table {}. Plrs: {} Avg Pot: ${} Plrs/Flop: {}".format(table['name'],
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
            log.debug("Table {} was scaned. Plrs: {} Entrs: {}".format(table['name'],
                                                                       table['unique_player_count'],
                                                                       table['entry_count'],
                                                                       ))
            tables.append(table)
        log.info("Scanner '{}' has scanned {} tables".format(settings.scanner_name, len(tables)))
        scan_result['scanner_name'] = settings.scanner_name
        scan_result['room'] = settings.pokerstars['room']
        scan_time =  datetime.datetime.now()
        scan_result['datetime'] = scan_time.isoformat()
        scan_result['tables'] = tables
        self._handle_scan(scan_result, scan_time)

    def _handle_scan(self, scan_result: dict, scan_time: datetime.datetime):
        scan_time = datetime.datetime.now()
        if self.save_only:
            try:
                self._save_scan_result(scan_result, scan_time)
            except FileNotFoundError:
                log.error("Can't save json file", exc_info=True)
        else:
            try:
                self._send_scan_result_to_api(scan_result)
            except Exception:
                pass

    def _save_scan_result(self, scan_result: dict,  scan_time: datetime.datetime):
        if self.to_file:
            file_name = 'scan_{}.json'.format(scan_time.strftime("%Y-%m-%d_%H-%M-%S"))
            with open(os.path.join(settings.json_dir, file_name), 'w') as file:
                json.dump(scan_result, file, indent=4)
        else:
            print(json.dumps(scan_result, indent=4))

    def _send_scan_result_to_api(self, scan_result: dict):
        pass

    def main_loop(self):
        repeat = True
        try:
            while repeat:
                try:
                    self.client.prepare()
                    self.scan_tables()
                except Exception:
                    log.error("Exception during scan", exc_info=True)
                self.client.save_datasets(include=self.library_for_saving)
                if self.only_once:
                    repeat = False
                    break
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


def add_args(parser: ArgumentParser):
    parser.add_argument('--save-only', dest='save_only', action='store_false',
                        help="Don't send a json file, only save", )
    parser.add_argument('--library_dir', dest='library_dir', default=None, help='Library directory')
    parser.add_argument('--only-once', '-o', dest='only_once', action='store_true', default=False,
                        help='scan only once')
    parser.add_argument('--save-characters', dest='save_characters', action='store_true', default=False,
                        help='Save character library')
    parser.add_argument('--save-flags', dest='save_flags', action='store_true', default=False, help='Save flag library')
    parser.add_argument('--only-tables', '-t', dest='only_tables', action='store_true', default=False,
                        help='Scan only tables')
    parser.add_argument('--verbose', action='store_true', default=False, help='Set logging level to "INFO"')
    parser.add_argument('--debug', action='store_true', default=False, help='Set logging level to "DEBUG"')


if __name__ == '__main__':
    parser = ArgumentParser(description='Pokerstars scanner')
    add_args(parser)
    args = parser.parse_args()
    if args.verbose:
        for l in [log, ocr.log, client.log]:
            l.setLevel(logging.INFO)
    if args.debug:
        for l in [log, ocr.log, client.log]:
            l.setLevel(logging.DEBUG)

    s = Scanner(save_only=args.save_only,
                library_dir=args.library_dir,
                only_once=args.only_once,
                save_characters=args.save_characters,
                save_flags=args.save_flags,
                only_tables=args.only_tables)
    s.main_loop()
