import logging

from pywinauto.application import Application, ProcessNotFoundError, AppStartError
from pywinauto import clipboard

PS_PATH = r'C:\Program Files (x86)\PokerStars\PokerStars.exe'

logging.basicConfig(level=logging.DEBUG)


class Client:
    def __init__(self, path=PS_PATH, main_window=None):
        self.path = path
        self.app = None
        self.main_window = None

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
            login_window = Window(self, title_re="Login.*")
            login_window.control.wait('visible', timeout=25)
            logging.info("The Login window is visible.")
            logging.info("Closing the Login window.")
            login_window.close()
            logging.info("Waiting for main window...")
            self.main_window = Window(self, title_re="PokerStars Lobby")
            self.main_window.control.wait('enabled', timeout=24)
            logging.info("Main window is enabled.")
        except AppStartError as e:
            print(e)
            return False
        return True

    def connect_or_start(self):
        if self.connect():
            return True
        else:
            return self.start()

    def is_running(self):
        if self.app is not None and self.app.is_process_running():
            return True
        return False


class Window:
    def __init__(self, client, title_re=None):
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


class List:
    def __init__(self, window, name, cursor=None, fields=None):
        self.control = window.control[name]
        self.has_next = False
        self.value = None
        self.previous_value = None
        self.reset()
        self.cursor = cursor
        if fields is not None:
            self.fields = list(fields)

    def __iter__(self):
        self.reset()
        value_dict = {}
        while self.has_next:
            value_dict['name'] = self.value
            yield value_dict
            self.get_next()

    def reset(self):
        self.control.type_keys('^{HOME}')
        self.has_next = True
        return self.get_value()

    def get_value(self):
        self.control.type_keys('^c')
        self.value = clipboard.GetData()
        return self.value

    def get_next(self):
        self.previous_value = self.value
        self.control.type_keys('{DOWN}')
        self.get_value()
        if self.previous_value is not None and self.previous_value == self.value:
            self.has_next = False
        return self.value

    def get_fields(self):
        pass


class ListField:

    CHARACTER = 0
    GRAPHIC = 1

    def __init__(self, name, field_type=CHARACTER):
        self.name = name
        self.first_x = 0
        self.last_x = 0
        self.value = None

