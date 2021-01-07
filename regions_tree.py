import urllib2
import json


class RegionsTree(object):
    def __init__(self, data):
        self.tree = data

    @classmethod
    def from_file(cls, fd):
        return cls(json.load(fd))

    @classmethod
    def from_remote(cls):
        return cls(cls._download_tree())

    def save_to_file(self, fd):
        json.dump(self.tree, fd)

    @classmethod
    def _get_westra_region_data(cls, region_id):
        url = 'http://westra.ru/passes/classificator.php?place=%s&export=json' % region_id
        res = urllib2.urlopen(url, timeout=60)
        return json.load(res)

    @classmethod
    def _download_tree(cls):
        top_level_regions  = cls._get_westra_region_data('0')
        return {
            'id': '0',
            'places': [cls._get_westra_region_data(region['id']) for region in top_level_regions],
            'title': 'World',
            'passes': []
        }

    def iterate_regions(self, region=None):
        if region is None:
            region = self.tree
        queue = [region]
        while queue:
            region = queue.pop()
            yield region
            queue.extend(region['places'])

    def iterate_passes(self, region=None):
        for region in self.iterate_regions(region):
            for pass_ in region['passes']:
                yield pass_

    def list_regions_at_level(self, level):
        regions = [self.tree]
        while level:
            regions2 = []
            for region in regions:
                if region['places']:
                    regions2.extend(region['places'])
                else:
                    regions2.append(region)
            regions = regions2
            level -= 1
        return regions
