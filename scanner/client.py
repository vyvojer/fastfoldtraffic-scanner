import logging
import logging.config
import re
import time
import warnings

import os
from PIL import Image
from pywinauto import clipboard
from pywinauto.application import Application, ProcessNotFoundError, AppStartError
import win32gui

from scanner.ocr import pil_to_opencv, ImageLibrary, ImageLogger, recognize_characters, recognize_flag, recognize_row
from scanner.ocr import FlagDoesNotExist, FlagTextIsNone, CharacterDoesNotExist, CharacterTextIsNone
from scanner import settings

logging.config.dictConfig(settings.LOGGING_CONFIG)
logging.setLoggerClass(ImageLogger)
log = logging.getLogger(__name__)

libraries = {}


class Client:
    def __init__(self, path=settings.POKERSTARS['path'],
                 main_window=None, library_dir=None):
        self.path = path
        self.app = None
        self.main_window = None
        self.player_list = None
        self.table_list = None
        self.library_dir = library_dir

    def connect(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.app = Application().connect(path=self.path)
        except ProcessNotFoundError:
            return False
        return True

    def start(self):
        try:
            logging.info("Starting PokerStars...")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                Application().start(self.path)
            self.app = Application().connect(path=self.path)
            logging.info("Waiting for the Login window...")
            login_window = ClientWindow(self, title_re="Login.*")
            login_window.control.wait('visible', timeout=180)
            logging.info("The Login window is visible.")
            logging.info("Closing the Login window.")
            login_window.close()
            logging.info("Waiting for main window...")
            self.main_window = ClientWindow(self, title_re="PokerStars Lobby")
            self.main_window.control.wait('enabled', timeout=120)
            logging.info("Main window is enabled.")
        except AppStartError as e:
            print(e)
            return False
        return True

    def prepare(self):
        self.connect_or_start()
        self.main_window = ClientWindow(self, title_re="PokerStars Lobby")
        self.move_main_window()
        for key, value in settings.POKERSTARS['libraries'].items():
            library_path = os.path.join(self.library_dir, value)
            libraries[key] = ImageLibrary(library_path=library_path)
        self.player_list = ClientList(self.main_window,
                                      settings.POKERSTARS['player_list'],
                                      row=ListRow.from_dict(settings.POKERSTARS['player_list_row']),
                                      items=ListItem.fields_from_dict(settings.POKERSTARS['player_fields']),
                                      )
        self.table_list = ClientList(self.main_window,
                                     settings.POKERSTARS['table_list'],
                                     row=ListRow.from_dict(settings.POKERSTARS['table_list_row']),
                                     items=ListItem.fields_from_dict(settings.POKERSTARS['table_fields']),
                                     )
        self.close_not_main_windows()

    def connect_or_start(self):
        if self.connect():
            return True
        else:
            return self.start()

    def move_main_window(self):
        self.main_window.control.restore()
        hwnd = self.main_window.control.handle
        default_width = settings.POKERSTARS['default_width']
        default_height = settings.POKERSTARS['default_height']
        x =  settings.POKERSTARS['default_x']
        y = settings.POKERSTARS['default_y']
        win32gui.MoveWindow(hwnd, x, y, default_width, default_height, True)

    def is_running(self):
        if self.app is not None and self.app.is_process_running():
            return True
        return False

    def save_datasets(self, include: list):
        if libraries:
            for key in libraries.keys():
                if key in include:
                    libraries[key].save_library()

    def close_not_main_windows(self):
        top_window = ClientWindow(self)
        if self.main_window.title != top_window.title:
            top_window.close()


class ClientWindow:
    def __init__(self, client, title_re=None):
        if title_re is None:
            self.control = client.app.top_window()
        else:
            self.control = client.app.window(title_re=title_re)

    @property
    def title(self):
        return self.control.texts()[0]

    @classmethod
    def from_control(cls, client, control):
        window = cls(client)
        window.control = control
        return window

    def __eq__(self, other):
        return self.control.get_properties() == other.control.get_properties()

    def __str__(self):
        return self.title

    def close(self):
        self.control.close()


class ListRow:
    def __init__(self, recognizer, zone):
        self.image = None
        self.recognizer = recognizer
        self.zone = zone

    def recognize(self, list_image):
        self.image = None
        self.image = self.recognizer(list_image, self.zone)

    @classmethod
    def from_dict(cls, field_dict: dict):
        parsed_dict = {}
        for key, value in field_dict.items():
            if key == 'recognizer':
                parsed_dict[key] = eval(value)
            else:
                parsed_dict[key] = value
        return cls(**parsed_dict)


class ClientList:
    def __init__(self, window, control_name, row=None, items=None):
        self.control = window.control[control_name]
        self.has_next = True
        self.clipboard = None
        self.previous_value = None
        self.row = row
        self.items = items
        self.image = None
        self.row: ListRow = row

    def __iter__(self):
        self.reset()
        while self.has_next:
            value_dict = dict()
            value_dict['name'] = self.clipboard
            if self.items is not None:
                for item in self.items:
                    value_dict[item.name] = item.value
            yield value_dict
            self.get_next()

    def reset(self):
        self.control.set_focus()
        self.control.type_keys('^{HOME}')
        self.has_next = True
        return self.get_row()

    def get_row(self):
        self.control.type_keys('^c')
        self.clipboard = clipboard.GetData()
        if self.items is not None and self.row is not None:
            for i in range(4):  # 4 attempts to read row
                if not self.get_items():
                    time.sleep(4)
                else:
                    self.control.type_keys('^c')
                    self.clipboard = clipboard.GetData()
                    break

        return self.clipboard

    def get_items(self):
        self.capture_as_image()
        try:
            log.debug("Recognizing row...")
            self.row.recognize(self.image)
        except ValueError:
            log.error("Can't recognize row.", extra={'images': [(self.image, 'wrong-row')]})
            return None
        else:
            log.debug("Row was recognized.", extra={'images': [(self.image, 'row')]})
            for item in self.items:
                item.recognize(self.row.image)
            return self.items

    def get_next(self):
        self.previous_value = self.clipboard
        self.control.type_keys('{DOWN}')
        self.get_row()
        if self.previous_value is not None and self.previous_value == self.clipboard:
            self.control.type_keys('{DOWN}')
            self.get_row()
            if self.previous_value is not None and self.previous_value == self.clipboard:
                self.has_next = False
        return self.clipboard

    def capture_as_image(self):
        self.set_pil_image(self.control.capture_as_image())

    def set_pil_image(self, pil_image: Image):
        self.image = pil_to_opencv(pil_image)


class ListItem:
    def __init__(self, name, zone=(0, 0), recognizer=None, parser=None, library=None, **kwargs):
        self.name = name
        self.zone = zone
        self.recognizer = recognizer
        self.parser = parser
        self.library = library
        self.kwargs = kwargs
        self.value = None

    def __repr__(self):
        cls_name = self.__class__.__name__
        repr_str = "{}(name={}, zone={}, recognizer={}, parser={}, {})"
        return repr_str.format(cls_name, self.name, self.zone,
                               self.recognizer.__name__, self.parser.__name__, **self.kwargs)

    def recognize(self, row_image):
        if self.recognizer:
            try:
                self.value = self.recognizer(row_image, self.zone, self.library, **self.kwargs)
            except FlagDoesNotExist as exc:
                log.warning("Was created new record in flag library",
                            extra={'images': [
                                (exc.cropped_image, 'created-flag-row'),
                                (exc.distinguished_image, 'created-flag-distinguished'),
                            ]})
                self.value = None
            except CharacterDoesNotExist as exc:
                log.warning("Was created new record in character library",
                            extra={'images': [
                                (exc.cropped_image, 'created-character-row'),
                                (exc.distinguished_image, 'created-character-distinguished'),
                            ]})
                self.value = None
            except FlagTextIsNone as exc:
                log.warning("Flag record text is none",
                            extra={'images': [
                                (exc.distinguished_image, 'flag-text-is-none'),
                            ]})
                self.value = None
            except CharacterTextIsNone as exc:
                log.warning("Character record text is none",
                            extra={'images': [
                                (exc.distinguished_image, 'character-text-is-none'),
                            ]})
                self.value = None
        if self.parser:
            self.value = self.parser(self.value)
        return self.value

    @classmethod
    def from_dict(cls, field_dict: dict):
        parsed_dict = {}
        for key, value in field_dict.items():
            if key == 'recognizer' or key == 'parser':
                log.debug('key={} value={}'.format(key, value))
                parsed_dict[key] = eval(value)
            elif key == 'library':
                parsed_dict[key] = libraries[value]
            else:
                parsed_dict[key] = value
        return cls(**parsed_dict)

    @classmethod
    def fields_from_dict(cls, fields_list):
        fields = []
        for field in fields_list:
            fields.append(ListItem.from_dict(field))
        return fields


def int_parser(initial_value):
    if initial_value is None:
        return None
    if initial_value == '':
        return 0
    int_str = ''.join(re.findall(r'\d', initial_value))
    try:
        return int(int_str)
    except ValueError:
        log.error("Cant convert '%s' to int", initial_value)
        return 0


def float_parser(initial_value):
    if initial_value is None:
        return None
    if initial_value == '':
        return 0
    float_str = ''.join(re.findall(r'\d|\.', initial_value))
    log.debug("Float initial_value={}, float_str={}".format(initial_value, float_str))
    try:
        return float(float_str)
    except ValueError:
        log.error("Cant convert '%s' to float", initial_value)
        return 0
