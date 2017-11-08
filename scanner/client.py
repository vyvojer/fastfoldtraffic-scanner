import logging
import logging.config
import re
import win32gui

from pywinauto import clipboard
from pywinauto.application import Application, ProcessNotFoundError, AppStartError
from scanner.osr import Osr, SymbolsDataset

from scanner import settings

logging.config.dictConfig(settings.logging_config)
log = logging.getLogger(__name__)


class Client:
    def __init__(self, path=settings.pokerstars['path'],
                 main_window=None):
        self.path = path
        self.app = None
        self.main_window = None
        self.player_list = None
        self.table_list = None
        self.dataset_dict = None

    def connect(self):
        try:
            self.app = Application().connect(path=self.path)
        except ProcessNotFoundError:
            return False
        return True

    def start(self):
        try:
            logging.info("Starting PokerStars...")
            Application().start(self.path)
            self.app = Application().connect(path=self.path)
            logging.info("Waiting for the Login window...")
            login_window = ClientWindow(self, title_re="Login.*")
            login_window.control.wait('visible', timeout=25)
            logging.info("The Login window is visible.")
            logging.info("Closing the Login window.")
            login_window.close()
            logging.info("Waiting for main window...")
            self.main_window = ClientWindow(self, title_re="PokerStars Lobby")
            self.main_window.control.wait('enabled', timeout=24)
            logging.info("Main window is enabled.")
        except AppStartError as e:
            print(e)
            return False
        return True

    def prepare(self):
        self.connect_or_start()
        self.main_window = ClientWindow(self, title_re="PokerStars Lobby")
        self.move_main_window()
        self.dataset_dict = {}
        for key, value in settings.pokerstars['dataset'].items():
            self.dataset_dict[key] = SymbolsDataset(value)
        self.player_list = ClientList(self.main_window,
                                      settings.pokerstars['player_list'],
                                      cursor=settings.pokerstars['player_list_cursor_zone'],
                                      fields=ListField.fields_from_dict(settings.pokerstars['player_fields']),
                                      dataset_dict=self.dataset_dict)
        self.table_list = ClientList(self.main_window,
                                     settings.pokerstars['table_list'],
                                     cursor=settings.pokerstars['table_list_cursor_zone'],
                                     fields=ListField.fields_from_dict(settings.pokerstars['table_fields']),
                                     dataset_dict=self.dataset_dict)
        self.close_not_main_windows()

    def connect_or_start(self):
        if self.connect():
            return True
        else:
            return self.start()

    def move_main_window(self):
        self.main_window.control.restore()
        hwnd = self.main_window.control.handle
        default_width = settings.pokerstars['default_width']
        default_height = settings.pokerstars['default_height']
        x = 100
        y = 100
        win32gui.MoveWindow(hwnd, x, y, default_width + x, default_height + y, True)

    def is_running(self):
        if self.app is not None and self.app.is_process_running():
            return True
        return False

    def save_datasets(self):
        if self.dataset_dict:
            for dataset in self.dataset_dict.values():
                dataset.save_dataset()

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


class ClientList:
    def __init__(self, window, control_name, cursor=None, fields=None, dataset_dict=None):
        self.control = window.control[control_name]
        self.has_next = True
        self.value = None
        self.previous_value = None
        self.cursor = cursor
        self.fields = fields
        self.dataset_dict = dataset_dict
#        self.reset()

    def __iter__(self):
        self.reset()
        while self.has_next:
            value_dict = {}
            value_dict['name'] = self.value
            if self.fields is not None:
                for field in self.fields:
                    value_dict[field.name] = field.parsed_value
            yield value_dict
            self.get_next()

    def reset(self):
        self.control.type_keys('^{HOME}')
        self.has_next = True
        return self.get_value()

    def get_value(self):
        self.control.type_keys('^c')
        self.value = clipboard.GetData()
        if self.fields is not None and self.cursor is not None:
            self.get_fields()
        return self.value

    def get_fields(self):
        pil_image = self.capture_as_image()
        osr = Osr(pil_image, self.cursor, self.fields, self.dataset_dict)
        try:
            osr.recognize_fields()
        except Exception:
            log.error("Can't recognize fields", exc_info=True)

    def get_next(self):
        self.previous_value = self.value
        self.control.type_keys('{DOWN}')
        self.get_value()
        if self.previous_value is not None and self.previous_value == self.value:
            self.control.type_keys('{DOWN}')
            self.get_value()
            if self.previous_value is not None and self.previous_value == self.value:
                self.has_next = False
        return self.value

    def capture_as_image(self):
        return self.control.capture_as_image()


class ListField:
    STRING = 0
    FLOAT = 1
    INT = 2
    GRAPHIC = 3

    def __init__(self, name, left_x, right_x, dataset_name, field_type=STRING, value=None):
        self.name = name
        self.left_x = left_x
        self.right_x = right_x
        self.field_type = field_type
        self.dataset_name = dataset_name
        self.value = value

    def __repr__(self):
        cls_name = self.__class__.__name__
        repr_str = "{}(name={}, left_x={}, right_x={}, vlaue={})"
        return repr_str.format(cls_name, self.name, self.left_x, self.right_x, self.value)

    @property
    def parsed_value(self):
        if self.field_type == self.INT:
            if self.value == '':
                return 0
            int_str = ''.join(re.findall(r'\d', self.value))
            try:
                return int(int_str)
            except ValueError:
                log.error("Cant convert '%s' to int", self.value)
                return 0
        elif self.field_type == self.FLOAT:
            if self.value == '':
                return 0
            int_str = ''.join(re.findall(r'\d|\.', self.value))
            try:
                return float(int_str)
            except ValueError:
                log.error("Cant convert '%s' to float", self.value)
                return 0
        else:
            return self.value

    @classmethod
    def from_dict(cls, field_dict):
        name = field_dict['name']
        left_x = field_dict['left_x']
        right_x = field_dict['right_x']
        dataset_name = field_dict.get('dataset_name', 'default')
        field_type = eval("ListField.{}".format(field_dict.get('field_type')))
        return cls(name, left_x, right_x, dataset_name, field_type=field_type)

    @classmethod
    def fields_from_dict(cls, fields_list):
        fields = []
        for field in fields_list:
            fields.append(ListField.from_dict(field))
        return fields
