import logging
import os.path

from decouple import AutoConfig

LOG_FILE = 'scan.log'
LOG_PICTURE_PATH = 'log_pictures'

if not os.path.exists(LOG_PICTURE_PATH):
    os.makedirs(LOG_PICTURE_PATH)

BASE_DIR = os.getcwd()
PACKAGE_DIR = os.path.dirname(os.path.realpath(__file__))

config = AutoConfig(search_path=BASE_DIR)

SCANNER_NAME = config('SCANNER_NAME', default='LOCAL')

JSON_DIR = config('JSON_DIR', default='.\\json')

API_HOST = config('API_HOST', default='https://fastfoldtraffic.com')
API_URL = config('API_URL', default='/api/v1/scans/')
API_VERIFY_SSL = config('API_VERIFY_SSL', cast=bool, default=False)
API_USER = config('API_USER', default='scanner')
API_PASSWORD = config('API_PASSWORD', default='scanner')

PAPERTRAIL_HOST = config('PAPERTRAIL_HOST', default='logs6.papertrailapp.com')
PAPERTRAIL_PORT = config('PAPERTRAIL_PORT', cast=int, default=12590)

POKERSTARS_PATH = config('POKERSTARS_PATH', default='C:\Program Files (x86)\PokerStars\PokerStars.exe')


LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)s - {} - %(name)s - %(levelname)s - %(message)s'.format(SCANNER_NAME),
                    'datefmt': '%Y-%m-%d %H:%M:%S'}
    },
    'handlers': {
        'console': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'level': logging.DEBUG,
            'class': 'logging.FileHandler',
            'mode': 'a',
            'formatter': 'default',
            'filename': LOG_FILE,

        },
        'syslog': {
            'level': logging.DEBUG,
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'default',
            'address': (PAPERTRAIL_HOST, PAPERTRAIL_PORT)
        },

    },
    'loggers': {
        '': {
            'level': logging.WARNING,
            'handlers': ['console', 'file', 'syslog']
        }
    },
    'disable_existing_loggers': False
}

POKERSTARS = {
    'path': POKERSTARS_PATH,
    'default_x': 70,
    'default_y': 0,
    'default_width': 1170,
    'default_height': 801,
    'main_window': 'PokerStars Lobby',
    'table_list': 'PokerStarsList0',
    'player_list': 'PokerStarsList2',
    'libraries': {'pokerstars_characters': 'pokerstars_characters.dat',
                  'pokerstars_flags': 'pokerstars_flags.dat'},
    'table_fields': [{'name': 'player_count',
                      'zone': (520, 570),
                      'recognizer': 'recognize_characters',
                      'parser': 'int_parser',
                      'library': 'pokerstars_characters',
                      },
                     {'name': 'average_pot',
                      'zone': (580, 650),
                      'recognizer': 'recognize_characters',
                      'parser': 'float_parser',
                      'library': 'pokerstars_characters',
                      },
                     {'name': 'players_per_flop',
                      'zone': (660, 730),
                      'recognizer': 'recognize_characters',
                      'parser': 'int_parser',
                      'library': 'pokerstars_characters',
                      },
                     ],
    'player_fields': [
        {'name': 'country',
         'zone': (140, 170),
         'recognizer': 'recognize_flag',
         'library': 'pokerstars_flags',
         },
        {'name': 'entries',
         'zone': (190, 220),
         'recognizer': 'recognize_characters',
         'parser': 'int_parser',
         'library': 'pokerstars_characters',
         },
    ],
    'table_list_row': {'zone': (450, 451),
                       'recognizer': 'recognize_row',
                       },
    'player_list_row': {'zone': (170, 171),
                        'recognizer': 'recognize_row',
                        },
    'room': 'PS'
}
