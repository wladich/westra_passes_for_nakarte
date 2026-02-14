# coding: utf-8
import re
from enum import StrEnum
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
    grade_season: NotRequired[Literal["winter"]]
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
    + "\u030a"
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


class Grade(StrEnum):
    # pylint: disable=invalid-name
    _1a = "1a"
    _1b = "1b"
    _2a = "2a"
    _2b = "2b"
    _3a = "3a"
    _3b = "3b"
    unknown = "unknown"
    nograde = "nograde"


normalized_grades = {
    # pylint: disable=protected-access
    "": Grade.unknown,
    "--": Grade.unknown,
    "1885": Grade.unknown,
    "1a": Grade._1a,
    "1a*": Grade._1a,
    "1a-1б": Grade._1a,
    "1a-2а": Grade._1a,
    "1а": Grade._1a,
    "1а*": Grade._1a,
    "1а*-1б": Grade._1a,
    "1а-1б": Grade._1a,
    "1а-2а": Grade._1a,
    "1а?": Grade._1a,
    "1б": Grade._1b,
    "1б*": Grade._1b,
    "1б*(?)": Grade._1b,
    "1б-1а": Grade._1a,
    "1б-1б*": Grade._1b,
    "1б-2а": Grade._1b,
    "1б-2б": Grade._1b,
    "1б?": Grade._1b,
    "1бальп": Grade._1b,
    "1блд": Grade._1b,
    "1бтур": Grade._1b,
    "1б-3а": Grade._1b,
    "2a": Grade._2a,
    "2a*": Grade._2a,
    "2a-2б": Grade._2a,
    "2а": Grade._2a,
    "2а*": Grade._2a,
    "2а-": Grade._2a,
    "2а-2б": Grade._2a,
    "2а-3а": Grade._2a,
    "2а?": Grade._2a,
    "2аальп": Grade._2a,
    "2б": Grade._2b,
    "2б(2": Grade._2b,
    "2б*": Grade._2b,
    "2б*(3а)": Grade._2b,
    "2б*-3а": Grade._2b,
    "2б-3а": Grade._2b,
    "2б?": Grade._2b,
    "3a": Grade._3a,
    "3a*": Grade._3a,
    "3aальп": Grade._3a,
    "3а": Grade._3a,
    "3а(": Grade._3a,
    "3а*": Grade._3a,
    "3а*-3б": Grade._3a,
    "3а,": Grade._3a,
    "3а-3": Grade._3a,
    "3а-3б": Grade._3a,
    "3аальп": Grade._3a,
    "3б": Grade._3b,
    "3б*": Grade._3b,
    "3б-3б*": Grade._3b,
    "3бальп": Grade._3b,
    "?": Grade.unknown,
    "~1а": Grade._1a,
    "~2a": Grade._2a,
    "~2а": Grade._2a,
    "н.к": Grade.nograde,
    "н.к.": Grade.nograde,
    "н/к": Grade.nograde,
    "н/к*": Grade.nograde,
    "н/к-1а": Grade.nograde,
    "н/к-1а?": Grade.nograde,
    "н/к-1б": Grade.nograde,
    "н/к?": Grade.nograde,
    "нк": Grade.nograde,
    "ок.1а": Grade._1a,
    "ок.1б": Grade._1b,
    "ок.2а": Grade._2a,
    "ок.2б": Grade._2b,
    "ок.3а": Grade._3a,
    "ок.3б": Grade._3b,
    "ос": Grade.unknown,
    "1бзальп": Grade._1b,
    "1б*альп": Grade._1b,
    "1б*!": Grade._1b,
    "1б!": Grade._1b,
    "1б*?": Grade._1b,
    "2а!": Grade._2a,
    "2а*!": Grade._2a,
    "1а*!": Grade._1a,
    "1атур": Grade._1a,
    "н/к*!": Grade.nograde,
}


def norm_grade(grade: str) -> Grade:
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
        is_grade_winter = False
        grade_eng = norm_grade(westra_pass["cat_sum"])
        grade = sanitize_text(westra_pass["cat_sum"])
        slopes = sanitize_text(westra_pass["type_sum"])
        if grade_eng == Grade.unknown:
            if (
                winter_grade_eng := norm_grade(westra_pass["cat_win"])
            ) != Grade.unknown:
                is_grade_winter = True
                grade_eng = winter_grade_eng
                grade = sanitize_text(westra_pass["cat_win"])
                slopes = sanitize_text(westra_pass["type_win"])
        nakarte_pass: NakartePass = {
            "id": check_is_int(westra_pass["id"]),
            "grade_eng": grade_eng,
            "latlon": get_latlon(westra_pass),
            "regions": [region["id"] for region in regions_path if region["id"] != "0"],
        }
        if pass_name := sanitize_text(westra_pass["title"]):
            nakarte_pass["name"] = pass_name
        if altnames := sanitize_text(westra_pass["other_titles"]):
            nakarte_pass["altnames"] = altnames
        if (elevation := westra_pass["height"]) not in ["", "0"]:
            nakarte_pass["elevation"] = check_is_int(elevation)
        if grade:
            nakarte_pass["grade"] = grade
        if is_grade_winter:
            nakarte_pass["grade_season"] = "winter"
        if slopes:
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
