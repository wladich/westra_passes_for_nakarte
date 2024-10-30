import argparse
import io
import json
import typing
import urllib.request

from mountain_passes_for_nakarte.fstr.catalogueparser import parse_catalog
from mountain_passes_for_nakarte.fstr.nakartewriter import convert_catalogue_for_nakarte

# pylint: disable-next=line-too-long
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1azG7VCU_zvEotb45JGnAJd5J4QI4JOM5_RojHwPyxgg/export?format=ods"


def write_passes(table_file: typing.BinaryIO, output_file: str) -> None:
    catalogue = parse_catalog(table_file)
    data = convert_catalogue_for_nakarte(catalogue)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def retrieve_table_file() -> typing.BinaryIO:
    with urllib.request.urlopen(SPREADSHEET_URL, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to download table, status {response.status}")
        data = response.read()
    return io.BytesIO(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file")
    parser.add_argument(
        "--local-table", type=argparse.FileType(mode="rb"), required=False
    )
    conf = parser.parse_args()
    table_file = conf.local_table if conf.local_table else retrieve_table_file()
    write_passes(table_file, conf.output_file)


if __name__ == "__main__":
    main()
