import argparse
import io
import urllib.request
from typing import Any, BinaryIO

from mountain_passes_for_nakarte import passes_coverage
from mountain_passes_for_nakarte.fstr.catalogueparser import parse_catalog
from mountain_passes_for_nakarte.fstr.nakartewriter import (
    NakartePassPoint,
    convert_catalogue_for_nakarte,
)
from mountain_passes_for_nakarte.utils import write_json_file_with_fixed_precision

# pylint: disable-next=line-too-long
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1azG7VCU_zvEotb45JGnAJd5J4QI4JOM5_RojHwPyxgg/export?format=ods"


def retrieve_table_file() -> BinaryIO:
    with urllib.request.urlopen(SPREADSHEET_URL, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to download table, status {response.status}")
        data = response.read()
    return io.BytesIO(data)


def build_coverage(passes: list[NakartePassPoint]) -> Any:
    points = [(p["latlon"][1], p["latlon"][0]) for p in passes]
    return passes_coverage.make_coverage_geojson(points)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_passes")
    parser.add_argument("output_coverage")
    parser.add_argument(
        "--local-table", type=argparse.FileType(mode="rb"), required=False
    )
    conf = parser.parse_args()
    table_file = conf.local_table if conf.local_table else retrieve_table_file()
    catalogue = parse_catalog(table_file)
    nakarte_data = convert_catalogue_for_nakarte(catalogue)
    write_json_file_with_fixed_precision(conf.output_passes, nakarte_data)
    coverage = build_coverage(nakarte_data["passes"])
    write_json_file_with_fixed_precision(conf.output_coverage, coverage)


if __name__ == "__main__":
    main()
