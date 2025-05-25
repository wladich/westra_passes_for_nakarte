# coding: utf-8
import re
from html import unescape
from typing import Literal, NotRequired, TypedDict

from .regions_tree import WestraComment, WestraPass, WestraRegion


class Comment(TypedDict):
    user: NotRequired[str]
    content: str


class NakartePass(TypedDict):
    id: str
    name: NotRequired[str]
    altnames: NotRequired[str]
    elevation: NotRequired[str]
    grade: NotRequired[str]
    grade_eng: str
    slopes: NotRequired[str]
    connects: NotRequired[str]
    is_summit: NotRequired[Literal[1]]
    latlon: tuple[float, float]
    comments: NotRequired[list[Comment]]
    author: NotRequired[str]
    reports_total: NotRequired[str]
    reports_photo: NotRequired[str]
    reports_tech: NotRequired[str]
    regions: list[str]


text_chars = re.compile(
    r'[-"?!+A-Za-z0-9 ,.():;/*~&[\]`%@'
    + "<>"
    + "\u0400-\u04ff"
    + "\u2116"
    + "\u2014"
    + "#_"
    + "\u2018\u2019\u2032"
    + "="
    + "\u2013"
    + "\u2026"
    + "\u2212"
    + "\u2033"
    + "\u0301"
    + "\u0100-\u01f7"
    + "\u00c0-\u00ff°«»'º“”±]"
)


def sanitize_text(s: str) -> str | None:
    s = unescape(unescape(s))
    s = s.strip()
    if s == "":
        return None
    s = (
        s.replace("\r", " ")
        .replace("\n", " ")
        .replace("&amp;", "&")
        .replace(r"\\'", "'")
        .replace(r"\'", "'")
        .replace("\xad", "")  # Soft hyphen
        .replace("\xa0", " ")  # Non-breaking space
        .replace("\t", " ")
    )
    for i, c in enumerate(s):
        if not text_chars.match(c):
            raise ValueError(f"Unexpected character #{i} {c!r} in string {s!r}")
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s


normalized_grades = {
    "": "unknown",
    "--": "unknown",
    "1885": "unknown",
    "1a": "1a",
    "1a*": "1a",
    "1a-1б": "1a",
    "1a-2а": "1a",
    "1а": "1a",
    "1а*": "1a",
    "1а*-1б": "1a",
    "1а-1б": "1a",
    "1а-2а": "1a",
    "1а?": "1a",
    "1б": "1b",
    "1б*": "1b",
    "1б*(?)": "1b",
    "1б-1а": "1a",
    "1б-1б*": "1b",
    "1б-2а": "1b",
    "1б-2б": "1b",
    "1б?": "1b",
    "1бальп": "1b",
    "1блд": "1b",
    "1бтур": "1b",
    "1б-3а": "1b",
    "2a": "2a",
    "2a*": "2a",
    "2a-2б": "2a",
    "2а": "2a",
    "2а*": "2a",
    "2а-": "2a",
    "2а-2б": "2a",
    "2а-3а": "2a",
    "2а?": "2a",
    "2аальп": "2a",
    "2б": "2b",
    "2б(2": "2b",
    "2б*": "2b",
    "2б*(3а)": "2b",
    "2б*-3а": "2b",
    "2б-3а": "2b",
    "2б?": "2b",
    "3a": "3a",
    "3a*": "3a",
    "3aальп": "3a",
    "3а": "3a",
    "3а(": "3a",
    "3а*": "3a",
    "3а*-3б": "3a",
    "3а,": "3a",
    "3а-3": "3a",
    "3а-3б": "3a",
    "3аальп": "3a",
    "3б": "3b",
    "3б*": "3b",
    "3б-3б*": "3b",
    "3бальп": "3b",
    "?": "unknown",
    "~1а": "1a",
    "~2a": "2a",
    "~2а": "2a",
    "н.к": "nograde",
    "н.к.": "nograde",
    "н/к": "nograde",
    "н/к*": "nograde",
    "н/к-1а": "nograde",
    "н/к-1а?": "nograde",
    "н/к-1б": "nograde",
    "н/к?": "nograde",
    "нк": "nograde",
    "ок.1а": "1a",
    "ок.1б": "1b",
    "ок.2а": "2a",
    "ок.2б": "2b",
    "ок.3а": "3a",
    "ок.3б": "3b",
    "ос": "unknown",
}

def norm_grade(grade: str) -> str:
    grade = grade.replace(" ", "").replace("\t", "").replace("\n", "").lower()
    if grade not in normalized_grades:
        raise ValueError(f"Unknown grade {grade!r}")
    return normalized_grades[grade]


def check_is_int(s: str) -> str:
    if not s.isdigit():
        raise ValueError(f"Not a digital value {s!r}")
    return s


def parse_is_summit(tech_type: str) -> bool:
    if tech_type == "1":
        return False
    if tech_type == "2":
        return True
    raise ValueError(f"Unexpected value {tech_type!r} for tech_type field")


def parse_latitude(lat_str: str) -> float:
    try:
        lat = float(lat_str)
        if not -90 < lat < 90:
            raise ValueError("Value not in range")
    except ValueError as exc:
        raise ValueError(f"Invalid latitude {lat_str!r}") from exc
    return lat


def parse_longitude(lon_str: str) -> float:
    try:
        lon = float(lon_str)
        if not -180 < lon < 180:
            raise ValueError("Value not in range")
    except ValueError as exc:
        raise ValueError(f"Invalid longitude {lon_str!r}") from exc
    return lon


def prepare_comments(raw_comments: list[WestraComment] | None) -> list[Comment]:
    comments: list[Comment] = []
    if not raw_comments:
        return comments
    for raw_c in raw_comments:
        content = sanitize_text(raw_c["title"])
        if not content:
            continue
        comment: Comment = {"content": content}
        user = sanitize_text(raw_c.get("user", ""))
        if user:
            comment["user"] = user
        comments.append(comment)
    return comments


def pass_has_coordinates(westra_pass: WestraPass) -> bool:
    has_lat = bool("latitude" in westra_pass)
    has_lon = bool("longitude" in westra_pass)
    if has_lat != has_lon:
        pass_id = westra_pass["id"]
        raise ValueError(f"Pass id={pass_id!r} has only one of latitude and longitude")
    return has_lat


def get_latlon(westra_pass: WestraPass) -> tuple[float, float]:
    return parse_latitude(westra_pass["latitude"]), parse_longitude(
        westra_pass["longitude"]
    )


def westra_pass_to_nakarte(
    westra_pass: WestraPass, regions_path: list[WestraRegion]
) -> NakartePass | None:
    # pylint: disable=too-many-branches, disable=too-many-locals
    if not pass_has_coordinates(westra_pass):
        return None
    if westra_pass["id"] == "12620":  # Test pass
        return None
    if westra_pass["height"] == "-150279":  # Test passes
        return None

    try:
        nakarte_pass: NakartePass = {
            "id": check_is_int(westra_pass["id"]),
            "grade_eng": norm_grade(westra_pass["cat_sum"]),
            "latlon": get_latlon(westra_pass),
            "regions": [region["id"] for region in regions_path if region["id"] != "0"],
        }
        if pass_name := sanitize_text(westra_pass["title"]):
            nakarte_pass["name"] = pass_name
        if altnames := sanitize_text(westra_pass["other_titles"]):
            nakarte_pass["altnames"] = altnames
        if (elevation := westra_pass["height"]) not in ["", "0"]:
            nakarte_pass["elevation"] = check_is_int(elevation)
        if grade := sanitize_text(westra_pass["cat_sum"]):
            nakarte_pass["grade"] = grade
        if slopes := sanitize_text(westra_pass["type_sum"]):
            nakarte_pass["slopes"] = slopes
        if connects := sanitize_text(westra_pass["connect"]):
            nakarte_pass["connects"] = connects
        if parse_is_summit(westra_pass["tech_type"]):
            nakarte_pass["is_summit"] = 1
        if comments := prepare_comments(westra_pass.get("comments")):
            nakarte_pass["comments"] = comments
        if author := sanitize_text(westra_pass["user_name"]):
            nakarte_pass["author"] = author
        if "reportStat" in westra_pass:
            if (reports_total := westra_pass["reportStat"]["total"]) != "0":
                nakarte_pass["reports_total"] = check_is_int(reports_total)
            if (reports_photo := westra_pass["reportStat"]["photo"]) != "0":
                nakarte_pass["reports_photo"] = check_is_int(reports_photo)
            if (reports_tech := westra_pass["reportStat"]["tech"]) != "0":
                nakarte_pass["reports_tech"] = check_is_int(reports_tech)
    except ValueError as exc:
        pass_id = westra_pass["id"]
        raise ValueError((f"Invalid pass id={pass_id!r}: {exc}")) from exc
    return nakarte_pass
