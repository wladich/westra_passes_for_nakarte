import argparse
import re
import xml.etree.ElementTree as ET
from typing import NamedTuple

from mountain_passes_for_nakarte.utils import write_json_with_float_precision


class LabelPoint(NamedTuple):
    latitude: str
    longitude: str
    title: str


def read_points_from_gpx(filename: str) -> list[LabelPoint]:
    s = open(filename).read()
    s = re.sub('\\sxmlns="[^"]+"', "", s, count=1)
    dom = ET.fromstring(s)
    points = []
    for wpt in dom.findall("wpt"):
        wpt_name = wpt.find("name")
        assert wpt_name
        title = wpt_name.text
        assert isinstance(title, str)
        points.append(
            LabelPoint(
                latitude=wpt.attrib["lat"], longitude=wpt.attrib["lon"], title=title
            )
        )
    return points


def save_points_to_geojson(filename: str, points: list[LabelPoint]) -> None:
    data = []
    for point in points:
        data.append(
            {
                "type": "Feature",
                "properties": {"name": point[2]},
                "geometry": {
                    "type": "Point",
                    "coordinates": [point[1], point[0]],
                },
            }
        )
    with open(filename, "w", encoding="utf-8") as f:
        write_json_with_float_precision(data, f, 5, ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    conf = parser.parse_args()

    points = read_points_from_gpx(conf.input)
    save_points_to_geojson(conf.output, points)
