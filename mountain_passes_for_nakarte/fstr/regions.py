# coding: utf-8
import csv
from pathlib import Path
from typing import NamedTuple

DATA_FILENAME = "regions.csv"
DATA_FILE_PATH = Path(__file__).parent / DATA_FILENAME


class Region(NamedTuple):
    id: int
    parent_region_name: str
    region_name: str
    worksheet_name: str
    url_suffix: str


regions: list[Region] = []
worksheet_titles_to_regions: dict[str, Region] = {}

with open(DATA_FILE_PATH, encoding="utf-8") as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader, 1):
        region = Region(i, *row)
        regions.append(region)
        worksheet_titles_to_regions[region.worksheet_name] = region
