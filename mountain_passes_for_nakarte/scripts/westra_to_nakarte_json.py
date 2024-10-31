import argparse

from mountain_passes_for_nakarte import passes_coverage
from mountain_passes_for_nakarte.utils import write_json_with_float_precision
from mountain_passes_for_nakarte.westra.pass_normalizers import westra_pass_to_nakarte
from mountain_passes_for_nakarte.westra.regions_tree import RegionsTree


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_passes")
    parser.add_argument("output_coverage")
    parser.add_argument("output_regions")
    parser.add_argument("--api-host", default="https://westra.ru")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--load-tree")
    source_group.add_argument("--api-key")
    conf = parser.parse_args()
    if conf.load_tree:
        with open(conf.load_tree, encoding="utf-8") as f:
            regions = RegionsTree.from_file(f)
    else:
        if not conf.api_key:
            parser.error("--api-key is required to load tree from server")
        regions = RegionsTree.from_remote(api_host=conf.api_host, api_key=conf.api_key)
    passes = []
    for westra_pass in regions.iterate_passes():
        nk_pass = westra_pass_to_nakarte(westra_pass)
        if nk_pass:
            passes.append(nk_pass)
    with open(conf.output_passes, "w", encoding="utf-8") as f:
        write_json_with_float_precision(passes, f, precision=6, ensure_ascii=False)

    points = [(p["latlon"][1], p["latlon"][0]) for p in passes]
    coverage = passes_coverage.make_coverage_geojson(points)
    with open(conf.output_coverage, "w", encoding="utf-8") as f:
        write_json_with_float_precision(coverage, f, precision=3, ensure_ascii=False)

    regions_names = []
    for level in [1, 2]:
        for region in regions.list_regions_at_level(level):
            for westra_pass in regions.iterate_passes(region):
                pass_ = westra_pass_to_nakarte(westra_pass)
                if pass_:
                    region_title = region["title"]
                    regions_names.append(f"{level}:{region_title}")
                    break
    with open(conf.output_regions, "w", encoding="utf-8") as f:
        f.write("\n".join(regions_names))


if __name__ == "__main__":
    main()
