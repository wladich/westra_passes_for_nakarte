import argparse
from regions_tree import RegionsTree
from utils import write_json_with_float_precision
from pass_normalizers import westra_pass_to_nakarte
from itertools import imap
import passes_coverage

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_passes')
    parser.add_argument('output_coverage')
    parser.add_argument('output_regions')
    parser.add_argument('--load-tree')
    parser.add_argument('--api-host', default='https://westra.ru')
    conf = parser.parse_args()
    if conf.load_tree:
        regions = RegionsTree.from_file(open(conf.load_tree))
    else:
        regions = RegionsTree.from_remote(api_host=conf.api_host)
    passes = filter(None, imap(westra_pass_to_nakarte, regions.iterate_passes()))
    with open(conf.output_passes, 'w') as f:
        write_json_with_float_precision(passes, f, precision=6, encoding='utf-8', ensure_ascii=False)

    points = [reversed(p['latlon']) for p in passes]
    covergae = passes_coverage.make_coverage_geojson(points)
    with open(conf.output_coverage, 'w') as f:
        write_json_with_float_precision(covergae, f, precision=3, encoding='utf-8', ensure_ascii=False)

    regions_names = []
    for level in [1, 2]:
        labels = []
        for region in regions.list_regions_at_level(level):
            for westra_pass in regions.iterate_passes(region):
                pass_ = westra_pass_to_nakarte(westra_pass)
                if pass_:
                    regions_names.append('%s:%s' % (level, region['title'].encode('utf-8')))
                    break
    with open(conf.output_regions, 'w') as f:
        f.write('\n'.join(regions_names))
