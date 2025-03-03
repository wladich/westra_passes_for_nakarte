import json
import urllib.request
from typing import Iterator, TextIO, TypedDict, cast


class WestraComment(TypedDict):
    id: str
    title: str
    user_id: str
    user: str
    add_time: str


class WestraReportStats(TypedDict):
    total: str
    tech: str
    photo: str
    mention: str
    coord: str
    first: str


class WestraPass(TypedDict):
    id: str
    tech_type: str
    title: str
    other_titles: str
    is_confirmed: str
    height: str
    cat_sum: str
    cat_win: str
    cat_spr: str
    cat_aut: str
    type_sum: str
    type_win: str
    type_spr: str
    type_aut: str
    connect: str
    class_number: str
    title_class: str
    height_class: str
    cat_class: str
    type_class: str
    connect_class: str
    comment_class: str
    first_asc_class: str
    user_id: str
    user_name: str
    beautyTitle: str
    latitude: str
    longitude: str
    coords_confirm: str
    reportStat: WestraReportStats
    comments: list[WestraComment]


class WestraRegion(TypedDict):
    id: str
    title: str
    places: list["WestraRegion"]
    passes: list[WestraPass]


class RegionsTree:
    default_api_host = "https://westra.ru"

    def __init__(self, data: WestraRegion):
        self.tree = data

    @classmethod
    def from_file(cls, fd: TextIO) -> "RegionsTree":
        return cls(json.load(fd))

    @classmethod
    def from_remote(cls, api_key: str, api_host: str | None = None) -> "RegionsTree":
        if api_host is None:
            api_host = cls.default_api_host
        return cls(cls._download_tree(api_key, api_host))

    def save_to_file(self, fd: TextIO) -> None:
        json.dump(self.tree, fd)

    @classmethod
    def _get_westra_region_data(
        cls, region_id: str, api_key: str, api_host: str
    ) -> WestraRegion:
        url = f"{api_host}/passes/classificator.php?place={region_id}&export=json&key={api_key}"
        with urllib.request.urlopen(url, timeout=60) as res:
            return cast(WestraRegion, json.load(res))

    @classmethod
    def _download_tree(cls, api_key: str, api_host: str) -> WestraRegion:
        top_level_regions = cast(
            list[WestraRegion], cls._get_westra_region_data("0", api_key, api_host)
        )
        assert isinstance(top_level_regions, list)
        return {
            "id": "0",
            "places": [
                cls._get_westra_region_data(region["id"], api_key, api_host)
                for region in top_level_regions
            ],
            "title": "World",
            "passes": [],
        }

    def iterate_regions(
        self, start_region: WestraRegion | None = None
    ) -> Iterator[list[WestraRegion]]:
        """Iterate regions with parents."""
        if start_region is None:
            start_region = self.tree
        queue = [[start_region]]
        while queue:
            region_path = queue.pop()
            yield region_path
            for region in region_path[-1]["places"]:
                queue.append(region_path + [region])

    def iterate_passes(
        self, region: WestraRegion | None = None
    ) -> Iterator[tuple[WestraPass, list[WestraRegion]]]:
        for region_path in self.iterate_regions(region):
            yield from ((pass_, region_path) for pass_ in region_path[-1]["passes"])

    def list_regions_at_level(self, level: int) -> list[WestraRegion]:
        regions = [self.tree]
        while level:
            regions2 = []
            for region in regions:
                if region["places"]:
                    regions2.extend(region["places"])
                else:
                    regions2.append(region)
            regions = regions2
            level -= 1
        return regions
