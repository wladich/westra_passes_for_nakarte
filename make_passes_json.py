# coding: utf-8
import csv
import json
import re
from HTMLParser import HTMLParser
import sys

unescape = HTMLParser().unescape


normalized_grades = {
    '1Б-2А': '2a',
    '1Б-2Б': '2b',
    'ок.3Б': '3b',
    'ок.3А': '3a',
    '1A-1Б': '1b',
    '1Б-1А': '1b',
    'н/к*': 'nograde',
    'ок.2А': '2a',
    '3Б*': '3b',
    '3А*': '3a',
    '1A': '1a',
    '1Б* (?)': '1b',
    '2Б(2': '2b',
    '3А (': '3a',
    '3A': '3a',
    'нк': 'nograde',
    '1А-1Б': '1b',
    '1A*': '1a',
    '2Б-3А': '3a',
    'н к': 'nograde',
    '1Бтур': '1b',
    '1Б*': '1b',
    '2Б*': '2b',
    '1Блд': '1b',
    '3А-3Б': '3b',
    'н/к-1А?': '1a',
    '1б-2а': '2a',
    '~2А': '2a',
    '2Б?': '2b',
    '1Б?': '1b',
    '2А-': '2a',
    '~2A': '2a',
    '3А,': '3a',
    '3А*-3Б': '3a',
    'н/к?': 'nograde',
    '1A-2А': '2a',
    '?': 'unknown',
    '2Б': '2b',
    '2А': '2a',
    '2 А': '2a',
    '~1А': '1a',
    '2А-3А': '3a',
    '3А': '3a',
    '3Б': '3b',
    '2А-2Б': '2b',
    'ок.2Б': '2b',
    '1Бальп': '1a',
    '2A': '2a',
    'ок.1Б': '1b',
    'ок.1А': '1a',
    '3Б-3Б*': '3b',
    '1А': '1a',
    '1Б': '1b',
    'н.к': 'nograde',
    '2Б*-3А': '3a',
    '2б': '2b',
    '1А*': '1a',
    '2Аальп': '2a',
    'н/к': 'nograde',
    '2А*': '2a',
    '3а': '3a',
    'Н/к*': 'nograde',
    '1А-2А': '2a',
    '2A*': '2a',
    '3А-3': '3a',
    '3Бальп': '3b',
    '2A-2Б': '2b',
    '1А?': '1a',
    '--': 'unknown',
    'ос': 'unknown',
    'н/к-1А': '1a',
    '1а': '1a',
    '1б': '1b',
    '2А?': '2a',
    '1885': 'unknown',
    '': 'unknown',
}


def norm_grade(row):
    s = row['cat_sum']
    s = s.strip()
    if not s in normalized_grades:
        raise ValueError('Unknown grade "%s" for pass id=%s' % (s, row['id']))
    return normalized_grades[s]


text_chars = re.compile(u'[-"?!+A-Za-z0-9 ,.():;/*~&[\]`%' +
                        u'\u0400-\u04ff' +
                        u'\u2116' +
                        u'#_' +
                        u'\u2018\u2019\u2032' +
                        u'=' +
                        u'\u2013' +
                        u'\u0100-\u01f7' +
                        u"\u00c0-\u00ff°«»']")


def sanitize_text(s, row):
    if isinstance(s, str):
        s2 = s.decode('utf-8')
    else:
        s2 = s
    s2 = unescape(unescape(s2))
    s2 = s2.strip()
    if s2 == '':
        return None
    s2 = s2.replace('\r', ' ')\
        .replace('\n', ' ')\
        .replace('&amp;', '&')\
        .replace(r"\'", "'")\
        .replace(u'\xad', '')\
        .replace('<', '&lt;')\
        .replace('>', '&gt;')\
        .replace('\t', ' ')
    for i, c in enumerate(s2):
        if not text_chars.match(c):
            raise ValueError('Unexpected character #%d %r in string "%r" for pass id=%s' % (i, c, s2, row['id']))
    s2 = re.sub(r'\s+', ' ', s2)
    s2 = s2.strip()
    return s2.encode('utf-8')


def check_boolean(s, row):
    if s in ('', '0'):
        return False
    if s == '1':
        return True
    raise ValueError('Unexpected value "%s" for boolean field for pass id=%s' % (s, row['id']))


def sanitize_int(s, row):
    if not s.isdigit():
        raise ValueError('Not digital value "%s" for pass id=%s' % (s, row['id']))
    return s


def get_is_summit(row):
    s = row['tech_type']
    if s == '1':
        return None
    if s == '2':
        return 1
    raise ValueError('Unexpected value "%s" for tech_type field for pass id=%s' % (s, row['id']))


def get_coords(row):
    lat = row['latitude']
    m = re.match(r'^N (\d+\.\d+)$', lat)
    if not m:
        raise ValueError('Invalid latitude "%s" for pass id=%s' % (lat, row['id']))
    lat = float(m.group(1))
    if not (-90 < lat < 90):
        raise ValueError('Invalid latitude "%s" for pass id=%s' % (lat, row['id']))
    lon = row['longitude']
    m = re.match(r'^E (\d+\.\d+)$', lon)
    if not m:
        raise ValueError('Invalid longitude "%s" for pass id=%s' % (lon, row['id']))
    lon = float(m.group(1))
    if not (-180 < lon < 180):
        raise ValueError('Invalid longitude "%s" for pass id=%s' % (lon, row['id']))
    return lat, lon


def row_to_item(row):
    comments = json.loads(row['comments'])
    comments2 = []
    for c in comments:
        comment = {'content': sanitize_text(c['title'], row)}
        if 'user' in c:
            comment['user'] = sanitize_text(c['user'], row)
        comments2.append(comment)

    item = {
        'name': sanitize_text(row['title'], row),
        'id': sanitize_int(row['id'], row),
        'altnames': sanitize_text(row['other_titles'], row),
        'elevation': sanitize_int(row['height'], row) if (row['height'] not in ('', '0')) else None,
        'grade': row['cat_sum'] or None,
        'grade_eng': norm_grade(row),
        'slopes': sanitize_text(row['type_sum'], row),
        'connects': sanitize_text(row['connect'], row),
        'is_summit': get_is_summit(row),
        'notconfirmed': not check_boolean(row['is_confirmed'], row) or None,
        'coords_notconfirmed': not check_boolean(row['coords_confirm'], row) or None,
        'latlon': get_coords(row),
        'comments': comments2 or None,
        'comment_class': sanitize_text(row['comment_class'], row),
        'author': sanitize_text(row['user_name'], row)
    }
    for k, v in item.items():
        if v is None:
            del item[k]
    return item


def make_json(dump_filename, json_filename):
    csv_reader = csv.DictReader(open(dump_filename))
    data = []
    for row in csv_reader:
        if row['latitude'] or row['longitude']:
            # FIXME: remove when fixed in db
            if row['tech_type'] == '0':
                continue
            if row['latitude'] == 'N 49':
                continue
            if row['height'] == '-2000':
                continue
            data.append(row_to_item(row))

    with open(json_filename, 'w') as f:
        json.dump(data, f, encoding='utf-8', ensure_ascii=False)

dump_filename = sys.argv[1]
json_filename = sys.argv[2]
make_json(dump_filename, json_filename)