# coding: utf-8
import urllib.request
from argparse import ArgumentParser

from .fstr_to_nakarte_json import SPREADSHEET_URL


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("filename", default=["fstr.ods"], nargs="*")
    conf = parser.parse_args()
    urllib.request.urlretrieve(SPREADSHEET_URL, conf.filename[0])


if __name__ == "__main__":
    main()
