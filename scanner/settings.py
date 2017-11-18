import logging
import os
import os.path

log_path = 'scan.log'
log_picture_path = 'log_pictures'

if not os.path.exists(log_picture_path):
    os.makedirs(log_picture_path)

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
            'filename': log_path,

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
    'default_width': 1070,
    'default_height': 701,
    'main_window': 'PokerStars Lobby',
    'table_list': 'PokerStarsList0',
    'player_list': 'PokerStarsList2',
    'libraries': {'pokerstars_characters': 'pokerstars_characters.dat',
                  'pokerstars_flags': 'pokerstars_flags.dat'},
    'table_fields': [{'name': 'player_count',
                      'zone': (520, 560),
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
                     {'name': 'hands_per_hour',
                      'zone': (790, 818),
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

json_dir = 'd:\\temp\\json'
