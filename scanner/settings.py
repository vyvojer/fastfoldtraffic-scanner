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
            'level': logging.DEBUG,
            'handlers': ['console', 'file']
        }
    },
    'disable_existing_loggers': False
}

pokerstars = {
    'path': r'C:\Program Files (x86)\PokerStars\PokerStars.exe',
    'default_width': 1070,
    'default_height': 701,
    'dataset': {'default': 'pokerstars_symbols.dat', 'flags': 'pokerstars_flags.dat'},
    'main_window': 'PokerStars Lobby',
    'table_list': 'PokerStarsList0',
    'player_list': 'PokerStarsList2',
    'table_fields': [{'name': 'players_count', 'left_x': 520, 'right_x': 560, 'field_type': 'INT'},
                     {'name': 'average_pot', 'left_x': 580, 'right_x': 650, 'field_type': 'FLOAT'},
                     {'name': 'players_flop', 'left_x': 660, 'right_x': 730, 'field_type': 'INT'},
                     {'name': 'hands_hour', 'left_x': 790, 'right_x': 818, 'field_type': 'INT'},
                     ],
    'player_fields': [{'name': 'country', 'left_x': 140, 'right_x': 170, 'field_type': 'PICTURE', 'dataset_name': 'flags'},
                      {'name': 'entries', 'left_x': 190, 'right_x': 220, 'field_type': 'INT'},
                      ],
    'table_list_cursor_zone': (450, 451),
    'player_list_cursor_zone': (170, 171),
    'room': 'PS'
}

json_dir = 'd:\\temp\\json'
