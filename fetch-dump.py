# -*- coding: utf-8 -*-
import urllib2
import csv
import json
import sys

pass_keys = [u'type_sum',
             u'coords_confirm',
             u'comment_class',
             u'height',
             u'connect',
             u'comments',
             u'type_aut',
             u'class_number',
             u'id',
             u'tech_type',
             u'type_class',
             u'user_id',
             u'is_confirmed',
             u'title',
             u'type_spr',
             u'cat_win',
             u'user_name',
             u'other_titles',
             u'cat_class',
             u'connect_class',
             u'beautyTitle',
             u'latitude',
             u'cat_sum',
             u'cat_aut',
             u'add_time',
             u'height_class',
             u'longitude',
             u'title_class',
             u'cat_spr',
             u'type_win',
             u'firstAscent']


def fetch_json(url):
    res = urllib2.urlopen(url)
    return json.load(res)


class PassWriter(object):
    def __init__(self, filename, fieldnames):
        self.f = open(filename, 'w')
        self.csv = csv.DictWriter(self.f, fieldnames)
        self.csv.writeheader()

    def write(self, obj):
        encoded = dict((k, v.encode('utf-8')) for k, v in obj.items())
        self.csv.writerow(encoded)

    def close(self):
        self.f.close()


def load_top_regions():
    regions = {}
    for item in fetch_json('http://westra.ru/passes/classificator.php?place=0&export=json'):
        region_id = item['id']
        regions[region_id] = {'name': item['title'], 'parent_id': None, 'id': region_id}
    return regions


def process_region(region, parent_id, regions, passes_writer):
    region_id = region['id']
    regions[region_id] = {'name': region['title'], 'parent_id': parent_id, 'id': region_id}
    for r in region['places']:
        process_region(r, region_id, regions, passes_writer)
    for obj in region['passes']:
        if 'comments' not in obj:
            obj['comments'] = '[]'
        else:
            obj['comments'] = json.dumps(obj['comments'])
        if 'firstAscent' not in obj:
            obj['firstAscent'] = '[]'
        else:
            obj['firstAscent'] = json.dumps(obj['firstAscent'])
        if ('latitude' not in obj) and ('longitude' not in obj) and ('coords_confirm' not in obj):
            obj['latitude'] = ''
            obj['longitude'] = ''
            obj['coords_confirm'] = '0'
        extraneous_keys = set(obj.keys()) - set(pass_keys)
        if extraneous_keys:
            raise ValueError('Unexpected keys in pass object: %s' % extraneous_keys)
        missing_keys = set(pass_keys) - set(obj.keys())
        if missing_keys:
            raise ValueError('Keys missing in pass object: %s' % missing_keys)

        obj['region_id'] = region_id
        passes_writer.write(obj)


def fetch_region(region_id):
    url = 'http://westra.ru/passes/classificator.php?place=%s&export=json' % region_id
    return fetch_json(url)


def dump_to_csv(passes_filename):
    regions = load_top_regions()
    passes_writer = PassWriter(passes_filename, pass_keys + ['region_id'])

    for region_id in regions.keys():
        process_region(fetch_region(region_id), None, regions, passes_writer)
    passes_writer.close()
    # with open(regions_filename, 'w') as f:
    #     json.dump(regions, f, indent=4)

passes_filename = sys.argv[1]
dump_to_csv(passes_filename)
# regions_filename = 'data/westra_regions.json'
# passes_filename = 'data/westra_passes.csv'

