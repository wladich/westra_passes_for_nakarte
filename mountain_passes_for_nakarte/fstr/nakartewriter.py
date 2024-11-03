# coding: utf-8
import re
from collections import defaultdict
from typing import TypedDict

from .catalogueparser import CatalogueRecord, Coordinates
from .regions import regions
from .utils import report_error

COORDS_PRECISION = 5


class NakartePassDetailsRow(TypedDict):
    number: str
    name: str
    altnames: str
    elevation: str
    surface_type: str
    connects: str
    coords: str
    approx_coords: str
    first_visit: str
    comment: str


class NakartePassPoint(TypedDict):
    latlon: tuple[float, float]
    point_grade: str
    point_name: str
    region_id: str
    details: list[NakartePassDetailsRow]


class NakarteRegion(TypedDict):
    name: str
    url: str


class NakarteData(TypedDict):
    passes: list[NakartePassPoint]
    regions: dict[str, NakarteRegion]


def is_name_of_main_point(name: str) -> bool:
    return bool(
        name == ""
        or re.search(r"\b(перевал|пер\.|седловина|седл\.?)\b", name, re.IGNORECASE)
    )


def get_map_point_coordinate(
    points: dict[str, Coordinates]
) -> tuple[Coordinates | None, str | None]:
    main_coordinate = None
    for name, coord in points.items():
        if is_name_of_main_point(name):
            if main_coordinate is not None:
                return None, "multiple coordinates for map point"  # type: ignore[unreachable]
            main_coordinate = coord
    if main_coordinate is None:
        return None, "no coordinates for map point"
    return main_coordinate, None


def convert_catalogue_for_nakarte(records: list[CatalogueRecord]) -> NakarteData:
    nakarte_regions = {
        str(region.id): NakarteRegion(name=region.region_name, url=region.url_suffix)
        for region in regions
    }

    points: defaultdict[Coordinates, list[CatalogueRecord]] = defaultdict(list)
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
        points[coord].append(catalogue_record)

    passes = []
    for coords, catalogue_records in points.items():
        first_record = catalogue_records[0]
        first_name = first_record.name
        first_region = first_record.region

        grades: set[str] = set()
        details = []

        for catalogue_record in catalogue_records:
            if catalogue_record.region != first_region:
                report_error(
                    "Different regions for one point",
                    first_region.worksheet_name,
                    first_record.index_number,
                    catalogue_record.region.worksheet_name,
                    catalogue_record.index_number,
                )
                continue
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
            grades.update(catalogue_record.normalized_grades)
            details.append(
                NakartePassDetailsRow(
                    number=catalogue_record.index_number,
                    name=catalogue_record.name,
                    altnames=catalogue_record.altnames,
                    elevation=catalogue_record.elevation,
                    surface_type=catalogue_record.surface_type,
                    connects=catalogue_record.connects,
                    coords=catalogue_record.coordinates,
                    approx_coords=catalogue_record.approximate_coordinates,
                    first_visit=catalogue_record.first_visit,
                    comment=catalogue_record.comment,
                )
            )
        pass_point = NakartePassPoint(
            latlon=(
                round(coords.latitude, COORDS_PRECISION),
                round(coords.longitude, COORDS_PRECISION),
            ),
            point_grade=min(grades),
            point_name=first_name,
            region_id=str(first_region.id),
            details=details,
        )
        passes.append(pass_point)
    return {"passes": passes, "regions": nakarte_regions}
