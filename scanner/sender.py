import requests
import json
import datetime
import logging.config
import os.path
from argparse import ArgumentParser

from scanner import settings

logging.config.dictConfig(settings.LOGGING_CONFIG)
log = logging.getLogger("scanner.sender")


def send_scan_result_to_api(scan_result: dict, scan_time: datetime.datetime = None, resending=False):
    successfully = True
    url = settings.API_HOST + settings.API_URL
    try:
        response = requests.put(url=url,
                                verify=settings.API_VERIFY_SSL,
                                data=json.dumps(scan_result),
                                headers={'content-type': 'application/json'},
                                auth=(settings.API_USER, settings.API_PASSWORD))
        if not response.ok:
            successfully = False
            log.error("Response status code is 400. Errors: {}...".format(response.text[:100]))
            response.raise_for_status()
    except requests.RequestException as e:
        successfully = False
        if resending:
            log.error("Can't send request.", exc_info=True)
        else:
            log.error("Can't send request. The json file will saved", exc_info=True)
            save_scan_result(scan_result, scan_time, was_sent=False)
    else:
        log.info("Scan result was successfully sent")
        if not resending:
            save_scan_result(scan_result, scan_time, was_sent=True)
    return successfully


def save_scan_result(scan_result: dict, scan_time: datetime.datetime, was_sent=True):
    if was_sent:
        save_dir = settings.JSON_SENT_DIR
    else:
        save_dir = settings.JSON_DIR
    file_name = 'scan_{}.json'.format(scan_time.strftime("%Y-%m-%d_%H-%M-%S"))
    try:
        with open(os.path.join(save_dir, file_name), 'w') as file:
            json.dump(scan_result, file, indent=4)
    except FileNotFoundError:
        log.error("Can't save json file", exc_info=True)
    else:
        log.info("Scan result was saved")


def send_saved():
    for file in sorted(os.listdir(settings.JSON_DIR), reverse=True):
        scan_result = json.load(open(os.path.join(settings.JSON_DIR, file)))
        if send_scan_result_to_api(scan_result, resending=True):
            src = os.path.join(settings.JSON_DIR, file)
            dst = os.path.join(settings.JSON_SENT_DIR, file)
            try:
                os.rename(src, dst)
            except FileExistsError:
                os.remove(src)


def add_args(parser: ArgumentParser):
    parser.add_argument('--verbose', action='store_true', default=False, help='Set logging level to "INFO"')
    parser.add_argument('--debug', action='store_true', default=False, help='Set logging level to "DEBUG"')


if __name__ == '__main__':
    parser = ArgumentParser(description='Scans sender')
    add_args(parser)
    args = parser.parse_args()
    if args.verbose:
        for l in [log,]:
            l.setLevel(logging.INFO)
    if args.debug:
        for l in [log,]:
            l.setLevel(logging.DEBUG)
    send_saved()