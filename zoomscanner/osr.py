from collections import namedtuple
import pickle
from tkinter import Tk, Label, Button, Entry
from PIL import Image, ImageTk
import cv2
import numpy as np

import os

FILE = 'symbols.dat'
COUNT = 0
COUNT_SMALL = 0


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


def pil2opencv(pil_image: Image) -> cv2:
    open_cv_image = np.array(pil_image.convert('RGB'))
    return open_cv_image


def get_list_zones(pil_image: Image, header='tables') -> dict:
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

    if header == 'tables':
        list_zones['stars'] = zones_list[9]
        list_zones['table'] = zones_list[8]
        list_zones['stakes'] = zones_list[7]
        list_zones['game'] = zones_list[6]
        list_zones['type'] = zones_list[5]
        list_zones['plrs'] = zones_list[4]
        list_zones['avg_pot'] = zones_list[3]
        list_zones['plrs_flop'] = zones_list[2]
        list_zones['hands_hour'] = zones_list[1]
        list_zones['scroller'] = zones_list[0]
    print(list_zones)
    return list_zones


def recognize_fields(pil_image: Image, list_zones: dict, ps_list='tables') -> dict:
    original = pil2opencv(pil_image)
    fields = {}
    if ps_list == 'tables':
        top, bottom = find_cursor(original[:, list_zones['plrs'] - 10: list_zones['plrs'] - 2])
    else:
        top, bottom = find_cursor(original[:, list_zones['plrs'] - 10: list_zones['plrs'] - 2])
    list_line = original[top: bottom, :]
    name_image = list_line[:, list_zones['table']:list_zones['stakes']]
    fields['name'] = recognize_text(name_image)
    return fields


def recognize_text(image):
    global COUNT
    COUNT = COUNT + 1
    cv2.imwrite("d:\\temp\\scanner\\image_{}.png".format(COUNT), image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    i, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    text = ""
    rects = []
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        rects.append((x, y, w, h))
    for (x, y, w, h) in sorted(rects, key=lambda x: x[0]):
        symbol_image = thresh[y:y + h, x:x + w]
        symbol = find_symbol((w, h), symbol_image)
        text = text + str(symbol)
    return text


def find_symbol(size, symbol_image):
    global COUNT_SMALL
    COUNT_SMALL = COUNT_SMALL + 1
    if not os.path.exists("d:\\temp\\scanner\\{}".format(COUNT)):
        os.makedirs("d:\\temp\\scanner\\{}".format(COUNT))
    cv2.imwrite("d:\\temp\\scanner\\{}\\image_{}.png".format(COUNT, COUNT_SMALL), symbol_image)
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
    [x, y, w, h] = cv2.boundingRect(contours[0])
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
            self.train()

    def train(self):
        symbol_record = self.sym_list[self.index]
        if self.entry.get() != '':
            symbol_record.symbol = self.entry.get()

        if self.index < len(self.sym_list):
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
