import argparse
from regions_tree import RegionsTree
from pass_normalizers import westra_pass_to_nakarte

DEBUG_LOAD_FILE = None


def centroid(points):
    x, y = zip(*points)
    x = sum(x) / len(points)
    y = sum(y) / len(points)
    return x, y


def write_gpx(fd, points):
    gpx = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>',
       '<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">']
    for point in points:
        gpx.append('<wpt lat="{lat}" lon="{lon}"><name>{name}</name></wpt>'.format(lat=point[0], lon=point[1], name=point[2].encode('utf-8')))
    gpx.append('</gpx>')
    fd.write('\n'.join(gpx))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_base_name')
    conf = parser.parse_args()
    if DEBUG_LOAD_FILE:
        regions = RegionsTree.from_file(open(DEBUG_LOAD_FILE))
    else:
        regions = RegionsTree.from_remote()

    for level in [1, 2]:
        labels = []
        for region in regions.list_regions_at_level(level):
            points = []
            for westra_pass in regions.iterate_passes(region):
                pass_ = westra_pass_to_nakarte(westra_pass)
                if not pass_:
                    continue
                points.append(pass_['latlon'])
            if points:
                center = centroid(points)
                labels.append(center + (region['title'],))
        file_name = '%s_%s.gpx' % (conf.output_base_name, level)
        with open(file_name, 'w') as f:
            write_gpx(f, labels)
