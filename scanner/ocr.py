import logging.config
import pickle
import time
from collections import Counter
from tkinter import Tk, Label, Button, Entry
import os

import cv2
import numpy as np
from PIL import Image, ImageTk

from scanner import settings

TABLE_LIST = 0


class ImageLogger(logging.Logger):
    """ Extended logger, that saving opencv images if extra has 'images'

     """

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        if extra:
            images = extra.get('images')
            if images:
                tick = time.time()
                for img, prefix in images:
                    img_name = "{}-{}.png".format(prefix, tick)
                    cv2.imwrite(os.path.join(settings.log_picture_path, img_name), img)
                    msg += " Image saved under name {}".format(img_name)
        super()._log(level, msg, args, exc_info, extra, stack_info)

logging.config.dictConfig(settings.logging_config)
logging.setLoggerClass(ImageLogger)
log = logging.getLogger(__name__)
logging.getLogger('PIL').setLevel(logging.WARNING)


class ImageRecord:
    def __init__(self, image, text):
        self.image = image
        self.text = text

    def __repr__(self):
        return "SymbolRecord({}, {})".format(self.image, self.text)


class ImageLibrary:
    def __init__(self, file=None, records=None):
        if file is None:
            if records is None:
                self.records = {}
            else:
                self.records = records
        else:
            self.file = file
            self.load_library()

    def __iter__(self):
        for one_size_symbols in self.records.values():
            for symbol in one_size_symbols:
                yield symbol

    def __str__(self):
        total = len([record for record in self])
        unnamed = len([record for record in self if not record.text])
        repeats = Counter(record.text for record in self).most_common(2)
        return "ImageLibrary Total: {}; Unnamed: {}; Repeats: {}".format(total, unnamed, repeats)


    def get_symbol_record(self, symbol_image, max_difference=0):
        was_created = False
        appropiriate_size = self.records.setdefault(symbol_image.shape, list())
        for symbol_record in appropiriate_size:
            if np.count_nonzero(symbol_record.image != symbol_image) <= max_difference:
                symbol_record = symbol_record
                break
        else:
            was_created = True
            symbol_record = ImageRecord(symbol_image, None)
            appropiriate_size.append(symbol_record)
        return was_created, symbol_record

    def load_library(self):
        self.records = {}
        try:
            log.info("Opening dataset file ")
            with open(self.file, 'rb') as file:
                self.records = pickle.load(file)
        except FileNotFoundError:
            log.warning("Can't open dataset file.", exc_info=True)

    def save_library(self):
        pickle.dump(self.records, open(self.file, 'wb'))


def crop_image(image, y1, y2, x1, x2):
    return image[y1:y2, x1:x2]


def recognize_row(image, zone):
    """ Find current row in PokerStars list """
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cropped_image = gray_image[:, zone[0]:zone[1]]
    _, thresh_image = cv2.threshold(cropped_image, 200, 255, cv2.THRESH_BINARY_INV)
    _, contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 1:
        [x, y, w, h] = cv2.boundingRect(contours[0])
    else:
        raise ValueError("Can't recognize row")
    row_top = y
    row_bottom = y + h
    return image[row_top:row_bottom, :]


def recognize_characters(row_image, zone, library, **kwargs):
    log.info("Recognizing text...")
    cropped_image = crop_image(row_image, None, None, zone[0], zone[1])
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_image, 160, 255, cv2.THRESH_BINARY)
    _, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    text = ""
    intersected_rects = []
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        if w < 10:  # Remove unexpected big artefacts
            intersected_rects.append((x, y, w, h))
    intersected_rects.sort(key=lambda x: x[0])
    united_rects = _get_united(intersected_rects)
    for index, (x, y, w, h) in enumerate(united_rects):
        symbol_image = thresh[y:y + h, x:x + w]
        was_created, symbol = library.get_symbol_record(symbol_image)
        text += str(symbol.text)
        if index > 0 and _check_space(united_rects[index - 1], (x, y, w, h)):
            text += ' '
    return text


def recognize_flag(row_image, zone, library, **kwargs):
    cropped_image = crop_image(row_image, None, None, zone[0], zone[1])
    flag_image = _distinguish_flag(cropped_image)
    if flag_image.shape != (16, 22, 3) and flag_image.shape != (16, 18, 3):
        log.error("Wrong flag size", extra={'images': [(cropped_image, 'wrong-size-flag-field'),
                                                       (flag_image, 'wrong-size-flag-distinguished'),
                                                       ]})
        return None
    else:
        was_created, image_record = _find_flag(flag_image, library)
        if was_created:
            logging.warning("Was created new record in flag dataset",
                            extra={'images':[
                                (cropped_image, 'created-flag-row'),
                                (flag_image, 'created-flag-distinguished'),
                            ]})
        elif image_record.text is None:
            logging.warning("Flag record has None text",
                            extra={'images':[
                                (flag_image, 'created-flag-distinguished'),
                            ]})
        return image_record.text

def _find_flag(flag_image, library: ImageLibrary):
    was_created, image_record = library.get_symbol_record(flag_image, max_difference=120)
    return was_created, image_record


def _distinguish_flag(flag_field_image):
    min_color, max_color = _find_min_and_max_colors(flag_field_image)
    mask = cv2.inRange(flag_field_image, min_color, max_color)
    mask_inv = cv2.bitwise_not(mask)
    (x, y, w, h) = cv2.boundingRect(mask_inv)
    flag_image = flag_field_image[y:y + h, x:x + w]
    return flag_image


def _find_min_and_max_colors(pic):
    """ find upper and low colors of background """
    h, w, _ = pic.shape
    corners = []
    corners.append(pic[0:1, 0:1])
    corners.append(pic[0:1, w - 1:w])
    corners.append(pic[h - 2:h - 1, 0:1])
    corners.append(pic[h - 2:h - 1, w - 1:w])
    min_color = min(corners, key=lambda corner: corner.min())
    max_color = max(corners, key=lambda corner: corner.max())
    return min_color, max_color + 1


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
    def __init__(self, master, dataset_file, only_empty=True):
        self.dataset = ImageLibrary(file=dataset_file)
        self.master = master
        master.title("Train")
        self.only_empty = only_empty
        self.symbol_record = None
        self.label = Label(master)
        self.label.pack()
        self.entry = Entry(master)
        self.entry.pack()
        self.next_button = Button(master, text="Update", command=self.train)
        self.delete_button = Button(master, text="Reset", command=self.reset_iterator)
        self.close_button = Button(master, text="Exit", command=self.quit)
        self.delete_button.pack()
        self.next_button.pack()
        self.close_button.pack()
        self.iterator = None
        self.reset_iterator()

    def reset_iterator(self):
        if self.only_empty:
            self.iterator = iter((s_record for s_record in self.dataset if not s_record.text))
        else:
            self.iterator = iter(self.dataset)
        self.symbol_record = next(self.iterator)
        if self.symbol_record:
            self._update_label()

    def train(self):
        if self.entry.get() != '':
            self.symbol_record.text = self.entry.get()
        self.symbol_record = next(self.iterator)
        if self.symbol_record:
            self._update_label()
        else:
            self.next_button.config(state="disabled")

    def _update_label(self):
        ratio = 5
        new_dimension = (int(self.symbol_record.image.shape[1] * ratio), int(self.symbol_record.image.shape[0] * ratio))
        new_image = cv2.resize(self.symbol_record.image, new_dimension, interpolation=cv2.INTER_AREA)
        # new_image = cv2.bitwise_not(new_image)
        pil_image = Image.fromarray(new_image)
        image_tk = ImageTk.PhotoImage(pil_image)
        self.label.image = image_tk
        self.label.config(image=image_tk)

        self.entry.delete(0, 'end')
        if self.symbol_record.text is not None:
            self.entry.insert(0, self.symbol_record.text)
        self.entry.focus_set()

    def quit(self):
        self.dataset.save_library()
        self.master.quit()


def train_symbols():
    root = Tk()
    my_gui = TrainGUI(root, 'pokerstars_flags.dat')
    root.mainloop()


if __name__ == "__main__":
    train_symbols()
