import logging

log_path = 'scanner.log'

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
            'mode': 'w',
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

symbols_file = 'symbols.dat'