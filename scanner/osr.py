import logging.config
import pickle
from tkinter import Tk, Label, Button, Entry

import cv2
import numpy as np
from PIL import Image, ImageTk

from scanner import settings

PLAYER_LIST = 0
TABLE_LIST = 1

logging.config.dictConfig(settings.logging_config)
log = logging.getLogger(__name__)
logging.getLogger('PIL').setLevel(logging.WARNING)


class SymbolRecord:
    def __init__(self, image, text):
        self.image = image
        self.text = text

    def __repr__(self):
        return "SymbolRecord({}, {})".format(self.image, self.text)


class SymbolsDataset:
    def __init__(self, file=None, symbols=None):
        if file is None:
            if symbols is None:
                self.symbols = {}
            else:
                self.symbols = symbols
        else:
            self.file = file
            self.load_dataset()

    def get_symbol_record(self, symbol_image):
        appropiriate_size = self.symbols.setdefault(symbol_image.shape, list())
        for symbol_record in appropiriate_size:
            if np.array_equal(symbol_record.image, symbol_image):
                symbol_record =  symbol_record
                break
        else:
            symbol_record = SymbolRecord(symbol_image, None)
            appropiriate_size.append(symbol_record)
        return symbol_record

    def __iter__(self):
        for one_size_symbols in self.symbols.values():
            for symbol in one_size_symbols:
                yield symbol

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
    def __init__(self, pil_image: Image, cursor: tuple, fields: list, dataset_dict: dict):
        self.cursor = cursor
        self.fields = fields
        self.dataset_dict = dataset_dict
        self.origin_image = pil_to_opencv(pil_image)
        self.gray_image = cv2.cvtColor(self.origin_image, cv2.COLOR_BGR2GRAY)
        self.cursor_top = None
        self.cursor_bottom = None

    def recognize_fields(self):
        self._recognize_cursor()
        for field in self.fields:
            field.value = self._recognize_text(
                self.gray_image[self.cursor_top:self.cursor_bottom, field.left_x:field.right_x],
                self.dataset_dict[field.dataset_name])
        return self.fields

    def _recognize_cursor(self):
        log.info("Recognizing cursor...")
        cropped_image = self.gray_image[:, self.cursor[0]:self.cursor[1]]
        _, thresh_image = cv2.threshold(cropped_image, 200, 255, cv2.THRESH_BINARY_INV)
        _, contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 1:
            [x, y, w, h] = cv2.boundingRect(contours[0])
        else:
            log.error("Can't recognize cursor")
            raise ValueError("Can't recognize cursor")
        self.cursor_top = y
        self.cursor_bottom = y + h - 1
        return self.cursor_top, self.cursor_bottom

    @staticmethod
    def _recognize_text(text_image, dataset: SymbolsDataset):
        log.info("Recognizing text...")
        _, thresh = cv2.threshold(text_image, 160, 255, cv2.THRESH_BINARY)
        _, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        text = ""
        intersected_rects = []
        for cnt in contours:
            (x, y, w, h) = cv2.boundingRect(cnt)
            if w < 10:  # Remove unexpected big artefacts
                intersected_rects.append((x, y, w, h))
        intersected_rects.sort(key=lambda x: x[0])
        united_rects = Osr._get_united(intersected_rects)
        for index, (x, y, w, h) in enumerate(united_rects):
            symbol_image = thresh[y:y + h, x:x + w]
            symbol = dataset.get_symbol_record(symbol_image).text
            if index > 0 and Osr._check_space(united_rects[index - 1], (x, y, w, h)):
                text += ' '
            text += str(symbol)
        return text

    @staticmethod
    def _recognize_picture(picture_image, dataset: SymbolsDataset):
        background = picture_image[1:2, 1:2]
        mask = cv2.inRange(picture_image, background, background)
        mask_inv = cv2.bitwise_not(mask)
        (x, y, w, h) = cv2.boundingRect(mask_inv)
        symbol_image = picture_image[y:y + h, x:x + w]
        text = dataset.get_symbol_record(symbol_image).text
        return text

    @staticmethod
    def _has_intersection(rect, next_rect):
        return next_rect[0] <= rect[0] + rect[2] - 1

    @staticmethod
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

    @staticmethod
    def _get_united(intersected_rects):
        united_rects = []

        for bound_rect in intersected_rects:
            if len(united_rects) > 0:
                last_rect = united_rects[-1]
                if not Osr._has_intersection(last_rect, bound_rect):
                    united_rects.append(bound_rect)
                else:
                    united_rects[-1] = Osr._unite_intersected(last_rect, bound_rect)
            else:
                united_rects.append(bound_rect)

        return united_rects

    @staticmethod
    def _check_space(previous_rect, rect):
        previous_last_rect_x = previous_rect[0] + previous_rect[2] - 1
        rect_x = rect[0]
        if rect_x - previous_last_rect_x > 3:
            return True
        else:
            return False


def pil_to_opencv(pil_image: Image) -> cv2:
    open_cv_image = np.array(pil_image.convert('RGB'))
    return open_cv_image


def get_list_zones(pil_image: Image, ps_list=TABLE_LIST) -> dict:
    list_zones = dict()
    original = pil_to_opencv(pil_image)
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
        list_zones['scroller'] = zones_list[0] + 70
        print(list_zones)
    return list_zones


class TrainGUI:
    def __init__(self, master, dataset_file):
        self.dataset = SymbolsDataset(file=dataset_file)
        self.master = master
        master.title("Train")
        self.sym_list = []
        for sizes in self.dataset.symbols.keys():
            for symbol_record in self.dataset.symbols[sizes]:
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
        self.dataset.save_dataset()
        self.master.quit()


def train_symbols():
    root = Tk()
    my_gui = TrainGUI(root, 'pokerstars_symbols.dat')
    root.mainloop()


if __name__ == "__main__":
    train_symbols()
