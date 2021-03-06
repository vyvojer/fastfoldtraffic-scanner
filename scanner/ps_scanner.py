import datetime
import json
import logging.config
import os.path
import os
import sys
from argparse import ArgumentParser
import time


from scanner import settings, ocr, client, sender


logging.config.dictConfig(settings.LOGGING_CONFIG)
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
        self.save_only = save_only
        if library_dir is None:
            self.library_dir = settings.PACKAGE_DIR
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

    def scan_players(self, table):
        self.client.move_main_window()
        self.client.close_not_main_windows()
        players = []
        entries_count = 0
        unique_players_count = 0
        for player in self.client.player_list:
            unique_players_count += 1
            if player['entries'] is None:  # Some character wasn't recognized
                log.error("Can't recognize field 'entries' for player '%s' ", player['name'])
            else:
                entries_count += int(player['entries'])
                players.append(player)
            if player['country'] is None:
                log.warning("Player '%s' from table '%s' has unknown country", player['name'], table)
        return unique_players_count, entries_count, players

    def scan_tables(self):
        self.client.move_main_window()
        self.client.close_not_main_windows()
        tables = []
        log.debug("Start scanning tables...")
        start_datetime = datetime.datetime.now()
        total_player_count = 0
        for table in self.client.table_list:
            log.debug("Scanning table {}. Plrs: {} Avg Pot: ${} Plrs/Flop: {}".format(table['name'],
                                                                                      table['player_count'],
                                                                                      table['average_pot'],
                                                                                      table['players_per_flop'],
                                                                                      ))
            # Some character wasn't recognized
            all_recognized = True
            for key, value in table.items():
                if value is None:
                    log.error("Can't recognize field '%s' for table '%s' ", key, table['name'])
                    all_recognized = False
            if not all_recognized:
                log.error("Table '%s' was skipped", table['name'])
                continue
            if not self.only_tables and table['player_count'] > 0:
                unique_players_count, entries_count, players = self.scan_players(table['name'])
                if not self._is_players_count_almost_equal(table['player_count'], entries_count):
                    log.warning("Table '{}' has big difference between player count ({}) and entries count ({})".format(
                        table['name'], table['player_count'], entries_count))
                    continue
                table['unique_player_count'] = unique_players_count
                table['entry_count'] = entries_count
                table['players'] = players
            else:
                unique_players_count = 0
                table['unique_player_count'] = 0
                table['entry_count'] = 0
                table['players'] = []
            total_player_count += unique_players_count
            log.debug("Table {} was scaned. Plrs: {} Entrs: {}".format(table['name'],
                                                                       table['unique_player_count'],
                                                                       table['entry_count'],
                                                                       ))
            end_datetime = datetime.datetime.now()
            table['datetime'] = end_datetime.isoformat()
            tables.append(table)
            if total_player_count >= settings.SENDING_PLAYER_LIMIT:
                self._handle_scan(tables, start_datetime, end_datetime)
                total_player_count = 0
                tables = []
        log.info("Scanner '{}' has scanned {} tables".format(settings.SCANNER_NAME, len(tables)))
        if tables:
            self._handle_scan(tables, start_datetime, end_datetime)

    def _handle_scan(self, tables: list, start_datetime: datetime.datetime, end_datetime: datetime.datetime):
        scan_result = {}
        scan_result['scanner_name'] = settings.SCANNER_NAME
        scan_result['room'] = settings.POKERSTARS['room']
        scan_result['full'] = settings.FULL
        scan_result['start_datetime'] = start_datetime.isoformat()
        scan_result['end_datetime'] = end_datetime.isoformat()
        scan_result['tables'] = tables
        if self.save_only:
            sender.save_scan_result(scan_result, end_datetime, was_sent=False)
        else:
            sender.send_scan_result_to_api(scan_result, end_datetime)



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
        if players < 10:
            threshold = 0.7
        elif players < 25:
            threshold = 0.75
        elif players < 35:
            threshold = 0.8
        elif players < 55:
            threshold = 0.85
        elif players < 100:
            threshold = 0.9
        elif players < 150:
            threshold = 0.92
        else:
            threshold = 0.94
        delta = min(players, entries) / max(players, entries)
        if delta >= threshold:
            return True
        else:
            return False


def add_args(parser: ArgumentParser):
    parser.add_argument('--save-only', dest='save_only', action='store_true', default=False,
                        help="Don't send a json file, only save", )
    parser.add_argument('--library-dir', dest='library_dir', default=None, help='Library directory')
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

    else:
        s = Scanner(save_only=args.save_only,
                    library_dir=args.library_dir,
                    only_once=args.only_once,
                    save_characters=args.save_characters,
                    save_flags=args.save_flags,
                    only_tables=args.only_tables)
        s.main_loop()
