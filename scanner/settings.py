import logging
import logging.config
import os
import os.path
import configparser
import sys

log_file = 'scan.log'
ini_file = 'scanner.ini'
log_picture_path = 'log_pictures'
scanner_name = None
json_dir = None
package_dir = None

logging_config = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
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
            'filename': log_file,

        }
    },
    'loggers': {
        '': {
            'level': logging.WARNING,
            'handlers': ['console', 'file']
        }
    },
    'disable_existing_loggers': False
}

pokerstars = {
    'path': r'C:\Program Files (x86)\PokerStars\PokerStars.exe',
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

logging.config.dictConfig(logging_config)
log = logging.getLogger(__name__)


def setup():
    read_config()
    global package_dir
    package_dir = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(log_picture_path):
        os.makedirs(log_picture_path)


def read_config():
    if not os.path.exists(ini_file):
        config = configparser.ConfigParser()
        config['Scanner'] = {
            'name': 'scanner_1',
        }
        config['API'] = {
            'host': 'localhost',
            'url': '/api/v1/update-tables/',
        }
        config['papertrailapp.com'] = {
            'host': 'logsN.papertrailapp.com',
            'key': 'XXXX',
        }
        log.warning("Config file doesn't exist. New config file will created.")
        with open('scanner.ini', 'w') as config_file:
            config.write(config_file)
        sys.exit(0)
    else:
        config = configparser.ConfigParser()
        config.read(ini_file)
        global scanner_name
        global json_dir
        scanner_name = config['Scanner'].get('name', 'Ivan')
        json_dir = config['Scanner'].get('json_dir', './json')


setup()
