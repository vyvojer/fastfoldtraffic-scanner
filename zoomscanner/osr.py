from collections import namedtuple
import pickle
import logging
import logging.config

from tkinter import Tk, Label, Button, Entry
from PIL import Image, ImageTk
import cv2
import numpy as np

from zoomscanner import settings

FILE = 'symbols.dat'

PLAYER_LIST = 0
TABLE_LIST = 1

logging.config.dictConfig(settings.logging_config)
log = logging.getLogger(__name__)
logging.getLogger('PIL').setLevel(logging.WARNING)


class SymbolRecord:
    def __init__(self, image, symbol):
        self.image = image
        self.symbol = symbol


def load_symbols():
    symbols = {}
    try:
        with open(FILE, 'rb') as file:
            symbols = pickle.load(file)
    except FileNotFoundError:
        pass
    return symbols


def dump_symbols():
    pickle.dump(SYMBOLS, open(FILE, 'wb'))


SYMBOLS = load_symbols()


class SymbolsDataset:

    def __init__(self, file=None, symbols=None):
        if file is None:
            if symbols is None:
                self.symbols = {}
            else:
                self.symbols = None
        else:
            self.file = file

    def load_dataset(self):
        self.symbols = {}
        try:
            log.info("Opening dataset file ")
            with open(self.file, 'rb') as file:
                self.symbols = pickle.load(file)
        except FileNotFoundError:
            log.warning("Can't open dataset file.", exc_info=True)


    def save_dataset(self):
        pickle.dump(self.symbols, open(self.file, 'wb'))


class Osr:

    def __init__(self, pil_image: Image, cursor: tuple, fields: list):
        self.cursor = cursor
        self.fields = fields
        self.origin_image = pil2opencv(pil_image)
        self.gray_image = cv2.cvtColor(self.origin_image, cv2.COLOR_BGR2GRAY)
        self.cursor_top = None
        self.cursor_bottom = None

    def _recognize_cursor(self):
        log.info("Recognizing cursor...")
        cropped_image = self.gray_image[:, self.cursor[0]:self.cursor[1]]
        cv2.imwrite('cropped.png', cropped_image)
        _, thresh_image = cv2.threshold(cropped_image, 200, 255, cv2.THRESH_BINARY_INV)
        _, contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 1:
            [x, y, w, h] = cv2.boundingRect(contours[0])
        else:
            log.error("Can't recognize cursor")
            raise ValueError("Can't recognize cursor")
        self.cursor_top = y
        self.cursor_bottom = y + h - 1
        return self.cursor_top, self.cursor_bottom



def pil2opencv(pil_image: Image) -> cv2:
    open_cv_image = np.array(pil_image.convert('RGB'))
    return open_cv_image


def get_list_zones(pil_image: Image, ps_list=TABLE_LIST) -> dict:
    list_zones = dict()
    original = pil2opencv(pil_image)
    cropped = original[-5: -1, :]
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    i, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    zones_list = []
    for contour in contours:
        [x, y, w, h] = cv2.boundingRect(contour)
        zones_list.append(x)

    if ps_list == TABLE_LIST:
        list_zones['stars'] = zones_list[9]
        list_zones['table'] = zones_list[8]
        list_zones['stakes'] = zones_list[7]
        list_zones['game'] = zones_list[6]
        list_zones['type'] = zones_list[5]
        list_zones['plrs'] = zones_list[4]
        list_zones['avg_pot'] = zones_list[3]
        list_zones['plrs_flop'] = zones_list[2]
        list_zones['hands_hour'] = zones_list[1]
        list_zones['settings'] = zones_list[0]
    else:
        list_zones['player'] = zones_list[2]
        list_zones['country'] = zones_list[1]
        list_zones['entries'] = zones_list[0]
        list_zones['scroller'] = zones_list[0]  + 70
        print(list_zones)
    return list_zones


def recognize_fields(pil_image: Image, list_zones: dict, ps_list=TABLE_LIST) -> dict:
    original = pil2opencv(pil_image)
    fields = {}
    if ps_list == TABLE_LIST:
        top, bottom = find_cursor(original[:, list_zones['plrs'] - 10: list_zones['plrs'] - 2])
    else:
        top, bottom = find_cursor(original[:, list_zones['country'] - 10: list_zones['country'] - 2])
    if top:
        list_line = original[top: bottom, :]
    else:
        return fields
    if ps_list == TABLE_LIST:
        name_image = list_line[:, list_zones['table']:list_zones['stakes']]
        stakes_image = list_line[:, list_zones['stakes']:list_zones['game']]
        game_image = list_line[:, list_zones['game']:list_zones['type']]
        players_image = list_line[:, list_zones['plrs']:list_zones['avg_pot']]
        avg_pot_image = list_line[:, list_zones['avg_pot']:list_zones['plrs_flop']]
        plrs_flop_image = list_line[:, list_zones['plrs_flop']:list_zones['hands_hour']]
        hads_hour_image = list_line[:, list_zones['hands_hour']:list_zones['settings']]
        fields['name'] = recognize_text(name_image)
        fields['stakes'] = recognize_text(stakes_image)
        fields['game'] = recognize_text(game_image)
        fields['plrs'] = recognize_text(players_image)
        fields['avg_pot'] = recognize_text(avg_pot_image)
        fields['plrs_flop'] = recognize_text(plrs_flop_image)
        fields['hands_hour'] = recognize_text(hads_hour_image)
    else:
        name_image = list_line[:, list_zones['player']:list_zones['country']]
        fields['name'] = recognize_text(name_image)
    return fields


def _has_intersection(rect, next_rect):
    return next_rect[0] <= rect[0] + rect[2] - 1


def _unite_intersected(rect, next_rect):
    rect_x = rect[0]
    rect_y = rect[1]
    rect_w = rect[2]
    rect_h = rect[3]
    rect_last_x = rect_x + rect_w - 1
    rect_last_y = rect_y + rect_h - 1
    next_rect_x = next_rect[0]
    next_rect_y = next_rect[1]
    next_rect_w = next_rect[2]
    next_rect_h = next_rect[3]
    next_rect_last_x = next_rect_x + next_rect_w - 1
    next_rect_last_y = next_rect_y + next_rect_h - 1

    if rect_x < next_rect_x:
        united_x = rect_x
    else:
        united_x = next_rect_x

    if rect_y < next_rect_y:
        united_y = rect_y
    else:
        united_y = next_rect_y

    if rect_last_x > next_rect_last_x:
        united_w = rect_last_x - united_x + 1
    else:
        united_w = next_rect_last_x - united_x + 1

    if rect_last_y > next_rect_last_y:
        united_h = rect_last_y - united_y + 1
    else:
        united_h = next_rect_last_y - united_y + 1

    return united_x, united_y, united_w, united_h


def _get_united(intersected_rects):
    united_rects = []

    for bound_rect in intersected_rects:
        if len(united_rects) > 0:
            last_rect = united_rects[-1]
            if not _has_intersection(last_rect, bound_rect):
                united_rects.append(bound_rect)
            else:
                united_rects[-1] = _unite_intersected(last_rect, bound_rect)
        else:
            united_rects.append(bound_rect)

    return united_rects

def _check_spase(previous_rect, rect):
    previous_last_rect_x = previous_rect[0] + previous_rect[2] - 1
    rect_x = rect[0]
    if rect_x - previous_last_rect_x > 3:
        return True
    else:
        return False


def recognize_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    i, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    text = ""
    intersected_rects = []
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        if w < 10:  # Remove unexpected artefacts
            intersected_rects.append((x, y, w, h))
    intersected_rects.sort(key=lambda x: x[0])
    united_rects = _get_united(intersected_rects)
    for index, (x, y, w, h) in enumerate(united_rects):
        symbol_image = thresh[y:y + h, x:x + w]
        symbol = find_symbol((w, h), symbol_image)
        if index > 0 and _check_spase(united_rects[index - 1], (x, y, w, h)):
            text += ' '
        text += str(symbol)
    return text


def find_symbol(size, symbol_image):
    appropriate_list = SYMBOLS.setdefault(size, list())
    for symbol_record in appropriate_list:
        if np.array_equal(symbol_record.image, symbol_image):
            symbol = symbol_record.symbol
            break
    else:
        symbol = None
        appropriate_list.append(SymbolRecord(symbol_image, symbol))
    return symbol


def find_cursor(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    i, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 1:
        [x, y, w, h] = cv2.boundingRect(contours[0])
    else:
        return None
    top = y + 1
    bottom = y + h - 1
    return top, bottom


class TrainGUI:
    def __init__(self, master):
        self.master = master
        master.title("Train")
        self.sym_list = []
        for sizes in SYMBOLS.keys():
            for symbol_record in SYMBOLS[sizes]:
                if symbol_record.symbol is None:
                    self.sym_list.append(symbol_record)

        self.index = 0
        self.label = Label(master)
        self.label.pack()
        self.entry = Entry(master)
        self.entry.pack()
        self.next_button = Button(master, text="Update", command=self.train)
        self.delete_button = Button(master, text="Delete", command=self.train)
        self.close_button = Button(master, text="Exit", command=self.quit)
        self.delete_button.pack()
        self.next_button.pack()
        self.close_button.pack()

        if len(self.sym_list) > 0:
            self._update_label(self.sym_list[0])

    def train(self):
        symbol_record = self.sym_list[self.index]
        if self.entry.get() != '':
            symbol_record.symbol = self.entry.get()

        if self.index < len(self.sym_list) - 1:
            self.index += 1
            symbol_record = self.sym_list[self.index]
            self._update_label(symbol_record)
        else:
            self.next_button.config(state="disabled")

    def _update_label(self, symbol_record):
        ratio = 5
        new_dimension = (int(symbol_record.image.shape[1] * ratio), int(symbol_record.image.shape[0] * ratio))
        new_image = cv2.resize(symbol_record.image, new_dimension, interpolation=cv2.INTER_AREA)
        new_image = cv2.bitwise_not(new_image)
        pil_image = Image.fromarray(new_image)
        image_tk = ImageTk.PhotoImage(pil_image)
        self.label.image = image_tk
        self.label.config(image=image_tk)

        self.entry.delete(0)
        if symbol_record.symbol is not None:
            self.entry.insert(0, symbol_record.symbol)
        self.entry.focus_set()

    def quit(self):
        dump_symbols()
        self.master.quit()


def train_symbols():
    load_symbols()
    root = Tk()
    my_gui = TrainGUI(root)
    root.mainloop()


if __name__ == "__main__":
    train_symbols()
