# coding: utf-8
"""Read ods file with passes catalogue, verify, sanitize, and structure data."""
import re
import typing
from dataclasses import dataclass
from typing import NamedTuple

from .odsreader import OdsTable
from .regions import Region, regions, worksheet_titles_to_regions
from .utils import report_error, report_errors


class RowFields(NamedTuple):
    number: str
    name: str
    altnames: str
    elevation: str
    grade: str
    surface_type: str
    connects: str
    coords: str
    coords_approx: str
    first_visit: str
    comment: str


@dataclass(frozen=True)
class CoordinatesWithPrecision:
    latitude: float
    longitude: float
    exact: bool


@dataclass(frozen=True)
class CatalogueRecord:  # pylint: disable=too-many-instance-attributes
    """Sanitized and normalized catalogue record for parser result."""

    index_number: str
    region: Region
    name: str
    altnames: str
    elevation: str
    grade: str
    normalized_grades: list[str]
    surface_type: str
    connects: str
    coordinates: str
    approximate_coordinates: str
    normalized_coordinates: dict[str, CoordinatesWithPrecision]
    first_visit: str
    comment: str


IGNORED_WORKSHEETS = {
    "весь каталог",
    "-Иныльчек",
    "Первопроходы",
    "DO NOT DELETE - AutoCrat Job Settings",
    "-старый Безенги",
    "-Джунгарский Алатау",
    "Районы",
    "Лист28",
    "-Безенги",
    "Районы по Вестре",
    "NVScriptsProperties",
}

COLUMN_TITLES = [
    "Номер внутри региона",
    "Название",
    "Другие названия",
    "Высота",
    "Категория",
    "Характеристика",
    "Что соединяет и как расположен",
    "Координаты WGS84",
    "Приблизительные координаты WGS84",
    "Руководитель, город, год первопрохождения",
    "Дополнительная информация",
]

FORCE_HEADERS = {
    "1 3. Южные отроги Северо-Чуйского хребта",
    "Хребты Заилийский Алатау и Кунгей-Алатау",
    "восхождения на Эльбрус в туристских походах",
    "Северные отроги",
    "Южные отроги",
    "восхождения на в.Казбек",
    "Восточный Кавказ",
    "Западный Кавказ",
    "Высокий Атлас",
}

GRADES_TO_NORMALIZED = {
    "Н/К": "nograde",
    "НК": "nograde",
    "1А": "1a",
    "1Б": "1b",
    "2А": "2a",
    "2Б": "2b",
    "3А": "3a",
    "3Б": "3b",
}


def check_worksheets(table: OdsTable) -> list[list[str]] | None:
    """Check names of worksheets and return list of issues.

    Checks:
    - no worksheets with same names
    - all worksheets for regions are present
    - no unknown worksheets are present

    Returns list of errors.
    """
    errors = []
    seen_worksheet_names = set()
    for name in table.sheet_names:
        if name in seen_worksheet_names:
            errors.append(["Duplicate worksheet name", name])
        seen_worksheet_names.add(name)

    worksheet_names = set(table.sheet_names)
    expected_worksheet_names = set(region.worksheet_name for region in regions)

    for name in expected_worksheet_names - worksheet_names:
        errors.append(["Worksheet not found", name])

    for name in worksheet_names - expected_worksheet_names - IGNORED_WORKSHEETS:
        errors.append(["Unexpected worksheet", name])
    return errors or None


def normalize_grade(s: str) -> list[str] | None:
    s = s.upper()
    s = s.replace("*", "")
    s = s.replace("A", "А")
    s = re.sub("[- ,()]+", " ", s)
    grades = s.strip().split()
    normalized_grades = []
    for grade in grades:
        try:
            normalized_grades.append(GRADES_TO_NORMALIZED[grade])
        except KeyError:
            return None
    return normalized_grades


def normalize_coordinates_cell(
    s: str, is_coords_exact: bool
) -> tuple[dict[str, CoordinatesWithPrecision] | None, list[str] | None]:
    # pylint: disable=too-many-locals
    re_deg = "[°º˚⁰]"
    re_min = "[′'ʹ’´ꞌ]"
    re_dot = [".,"]
    re_text = r"[а-яА-Яa-zA-Z .,0-9()\n-]+"

    coordinates = {}
    i = 0
    while i < len(s):
        m = re.match(
            # pylint: disable=line-too-long
            rf"""^
            (?P<name>{re_text})?:?\s*
            (?P<lat_hemi>[NS])\ *(?P<lat_deg>\d+){re_deg}\ *(?P<lat_min_int>\d+){re_dot}(?P<lat_min_frac>\d+){re_min},?\s*
            (?P<lon_hemi>[EWЕ])\ *(?P<lon_deg>\d+){re_deg}\ *(?P<lon_min_int>\d+){re_dot}(?P<lon_min_frac>\d+){re_min},?\s*
        """,
            s[i:],
            re.VERBOSE,
        )
        if not m:
            return None, ["no coordinate found at position", str(i)]
        lat_deg = int(m.group("lat_deg"))
        lat_min_int = int(m.group("lat_min_int"))
        lat_min_frac = float("0.%s" % m.group("lat_min_frac"))
        lon_deg = int(m.group("lon_deg"))
        lon_min_int = int(m.group("lon_min_int"))
        lon_min_frac = float("0.%s" % m.group("lon_min_frac"))
        if lat_deg > 90 or lat_min_int > 60 or lon_deg > 180 or lon_min_int > 60:
            return None, ["coordinate field out of range"]
        lat = lat_deg + (lat_min_int + lat_min_frac) / 60
        lon = lon_deg + (lon_min_int + lon_min_frac) / 60
        if lat > 90 or lon > 180:
            return None, ["coordinates value out of range"]
        if m.group("lat_hemi") == "S":
            lat *= -1
        if m.group("lon_hemi") == "W":
            lon *= -1
        point_name = (m.group("name") or "").strip()
        if point_name in coordinates:
            return None, ["multiple coordinates with same name in one cell"]
        coordinates[point_name] = CoordinatesWithPrecision(
            latitude=lat, longitude=lon, exact=is_coords_exact
        )
        i += m.end()
    return coordinates or None, None


def normalize_coordinates(
    exact: str, approx: str
) -> tuple[dict[str, CoordinatesWithPrecision] | None, list[list[str]] | None]:
    errors = []
    if exact:
        exact_coordinates, error = normalize_coordinates_cell(
            exact, is_coords_exact=True
        )
        if error:
            errors.append([*error, repr(exact)])
    else:
        exact_coordinates = {}
    if approx:
        approx_coordinates, error = normalize_coordinates_cell(
            approx, is_coords_exact=False
        )
        if error:
            errors.append([*error, repr(approx)])
    else:
        approx_coordinates = {}
    if errors:
        return None, errors
    assert exact_coordinates is not None
    assert approx_coordinates is not None
    # Combine two dictionaries preserving order of items and ensuring that
    # exact coordinates go before the approximate ones.
    result = dict(exact_coordinates)
    for k, v in approx_coordinates.items():
        if k not in result:
            result[k] = v
    return result, None


def parse_catalog(table_file: typing.BinaryIO) -> list[CatalogueRecord]:
    # pylint: disable=too-many-branches,too-many-locals
    table = OdsTable(table_file)
    errors = check_worksheets(table)
    report_errors(errors, fatal=True)
    normalized_rows: list[CatalogueRecord] = []

    for sheet_index, sheet_name in enumerate(table.sheet_names):
        if sheet_name in IGNORED_WORKSHEETS:
            continue
        region = worksheet_titles_to_regions[sheet_name]
        rows = table.get_sheet_values(sheet_index)
        if rows[0] != COLUMN_TITLES:
            report_error(
                "Unexpected column header",
                region.worksheet_name,
                repr(rows[0]),
                fatal=True,
            )

        in_traverses_section = False
        for row in rows[1:]:
            row = [cell.strip() for cell in row]
            is_row_header = not any(row[1:])
            is_row_region_header = row[0] in FORCE_HEADERS or bool(
                re.match(r"[0-9][0-9.]*\s*[^ 0-9.][^0-9.]", row[0])
            )
            is_row_traverses_header = row[0].lower() == "траверсы"
            if is_row_header != (is_row_region_header != is_row_traverses_header):
                report_error(
                    "Unexpected header format",
                    region.worksheet_name,
                    repr(row),
                    fatal=True,
                )
            if is_row_traverses_header:
                in_traverses_section = True
                continue
            if is_row_region_header:
                in_traverses_section = False
                continue
            if in_traverses_section:
                continue
            row_fields = RowFields(*row)
            skip_row = False
            if not row_fields.coords and not row_fields.coords_approx:
                continue
            if not row_fields.name:
                report_error(
                    "Name is empty",
                    region.worksheet_name,
                    row_fields.number,
                    row_fields.name,
                )
            if "\n" in row_fields.name:
                report_error(
                    "Newline in pass name",
                    region.worksheet_name,
                    row_fields.number,
                    row_fields.name,
                )
            normalized_grades = normalize_grade(
                row_fields.grade,
            )
            if not normalized_grades:
                report_error(
                    "Malformed grade",
                    region.worksheet_name,
                    row_fields.number,
                    row_fields.grade,
                )
                skip_row = True
            normalized_coordinates, errors = normalize_coordinates(
                row_fields.coords, row_fields.coords_approx
            )
            if errors:
                report_errors(
                    [
                        [
                            *error[:-1],
                            region.worksheet_name,
                            row_fields.number,
                            error[-1],
                        ]
                        for error in errors
                    ]
                )
                skip_row = True
            if not re.match(r"^(\d{1,3}\.)+(\d{1,3})$", row_fields.number):
                report_error(
                    "Malformed number", region.worksheet_name, repr(row_fields.number)
                )
            if skip_row:
                continue
            assert normalized_coordinates
            assert normalized_grades
            normalized_rows.append(
                CatalogueRecord(
                    index_number=row_fields.number,
                    region=region,
                    name=row_fields.name,
                    altnames=row_fields.altnames,
                    elevation=row_fields.elevation,
                    grade=row_fields.grade,
                    normalized_grades=normalized_grades,
                    surface_type=row_fields.surface_type,
                    connects=row_fields.connects,
                    coordinates=row_fields.coords,
                    approximate_coordinates=row_fields.coords_approx,
                    first_visit=row_fields.first_visit,
                    comment=row_fields.comment,
                    normalized_coordinates=normalized_coordinates,
                )
            )

    return normalized_rows
