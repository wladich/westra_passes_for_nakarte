# coding: utf-8
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Collection, Literal, NotRequired, TypedDict

from .catalogueparser import CatalogueRecord, CoordinatesWithPrecision
from .regions import regions
from .utils import report_error


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


class NakartePassDetailsRow(TypedDict):
    # pylint: disable=duplicate-code
    number: str
    name: str
    altnames: str
    elevation: str
    grade: str
    surface_type: str
    connects: str
    coords: str
    approx_coords: str
    first_visit: str
    comment: str


class NakartePassPoint(TypedDict):
    latlon: tuple[float, float]
    approx: NotRequired[Literal[True]]
    grade_min: str
    grade_max: NotRequired[str]
    elevation: NotRequired[int]
    name: str
    region_id: str
    details: list[NakartePassDetailsRow]


class NakarteRegion(TypedDict):
    name: str
    url: str


class NakarteData(TypedDict):
    passes: list[NakartePassPoint]
    regions: dict[str, NakarteRegion]


def is_exclusive_name_of_main_point(name: str) -> bool:
    return bool(name == "" or re.search(r"\b(перевал|пер\.)\b", name, re.IGNORECASE))


def is_non_exclusive_name_of_main_point(name: str) -> bool:
    return bool(re.search(r"\b(седловина|седл\.?)\b", name, re.IGNORECASE))


def get_map_point_coordinate(
    points: dict[str, CoordinatesWithPrecision]
) -> tuple[CoordinatesWithPrecision | None, str | None]:
    main_coordinate = None
    is_main_coordinate_from_exclusive_point = False
    for name, coord in points.items():
        if is_non_exclusive_name_of_main_point(name):
            if is_main_coordinate_from_exclusive_point:
                return None, "multiple coordinates for map point"
            if main_coordinate is None:  # use first such coordinate
                main_coordinate = coord
        elif is_exclusive_name_of_main_point(name):
            if main_coordinate is not None:
                return None, "multiple coordinates for map point"
            main_coordinate = coord
            is_main_coordinate_from_exclusive_point = True
    if main_coordinate is None:
        return None, "no coordinates for map point"
    return main_coordinate, None


def get_min_grade(grades: Collection[str]) -> str:
    if "nograde" in grades:
        return "nograde"
    return min(grades)


def get_max_grade(grades: Collection[str]) -> str:
    grades = set(grades)
    if len(grades) > 1:
        grades.discard("nograde")
    return max(grades)


def convert_catalogue_for_nakarte(records: list[CatalogueRecord]) -> NakarteData:
    # pylint: disable=too-many-locals
    nakarte_regions = {
        str(region.id): NakarteRegion(name=region.region_name, url=region.url_suffix)
        for region in regions
    }

    points: defaultdict[
        Coordinates, list[tuple[CatalogueRecord, CoordinatesWithPrecision]]
    ] = defaultdict(list)
    for catalogue_record in records:
        coord, error = get_map_point_coordinate(catalogue_record.normalized_coordinates)
        if error:
            report_error(
                error,
                catalogue_record.region.worksheet_name,
                catalogue_record.index_number,
                repr(catalogue_record.coordinates),
                repr(catalogue_record.approximate_coordinates),
            )
            continue
        assert coord is not None
        simple_coords = Coordinates(coord.latitude, coord.longitude)
        points[simple_coords].append((catalogue_record, coord))

    passes = []
    for catalogue_records in points.values():
        first_record = catalogue_records[0][0]
        first_name = first_record.name
        first_region = first_record.region
        first_coords = catalogue_records[0][1]

        grades: set[str] = set()
        elevations: set[str] = set()
        details = []

        for catalogue_record, record_map_coords in catalogue_records:
            if catalogue_record.region != first_region:
                report_error(
                    "Different regions for one point",
                    first_region.worksheet_name,
                    first_record.index_number,
                    catalogue_record.region.worksheet_name,
                    catalogue_record.index_number,
                )
                continue
            # It is important that first record has simple name as it is used for point
            # name JS part.
            if (
                catalogue_record.name != first_name
                and not catalogue_record.name.startswith(f"{first_name} + ")
            ):
                report_error(
                    "Different names for one point",
                    first_region.worksheet_name,
                    first_record.index_number,
                    catalogue_record.region.worksheet_name,
                    catalogue_record.index_number,
                    first_name,
                    catalogue_record.name,
                )
                continue
            assert (
                record_map_coords.longitude == first_coords.longitude
                and record_map_coords.latitude == first_coords.latitude
            )
            if record_map_coords.exact != first_coords.exact:
                report_error(
                    "Some coords are exact and some are approx for records in single point",
                    first_region.worksheet_name,
                    first_record.index_number,
                    catalogue_record.region.worksheet_name,
                    catalogue_record.index_number,
                )
            grades.update(catalogue_record.normalized_grades)
            elevations.add(catalogue_record.elevation)
            details.append(
                NakartePassDetailsRow(
                    number=catalogue_record.index_number,
                    name=catalogue_record.name,
                    altnames=catalogue_record.altnames,
                    elevation=catalogue_record.elevation,
                    grade=catalogue_record.grade,
                    surface_type=catalogue_record.surface_type,
                    connects=catalogue_record.connects,
                    coords=catalogue_record.coordinates,
                    approx_coords=catalogue_record.approximate_coordinates,
                    first_visit=catalogue_record.first_visit,
                    comment=catalogue_record.comment,
                )
            )
        min_grade = get_min_grade(grades)
        max_grade = get_max_grade(grades)
        pass_point = NakartePassPoint(
            latlon=(first_coords.latitude, first_coords.longitude),
            grade_min=min_grade,
            name=first_name,
            region_id=str(first_region.id),
            details=details,
        )
        if not first_coords.exact:
            pass_point["approx"] = True
        if min_grade != max_grade:
            pass_point["grade_max"] = max_grade
        if len(elevations) == 1 and (elevation := elevations.pop()).isdigit():
            pass_point["elevation"] = int(elevation)
        passes.append(pass_point)
    return {"passes": passes, "regions": nakarte_regions}
