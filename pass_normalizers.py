# coding: utf-8
import re
from HTMLParser import HTMLParser


unescape = HTMLParser().unescape


text_chars = re.compile(u'[-"?!+A-Za-z0-9 ,.():;/*~&[\]`%@' +
                        u'\u0400-\u04ff' +
                        u'\u2116' +
                        u'\u2014' +
                        u'#_' +
                        u'\u2018\u2019\u2032' +
                        u'=' +
                        u'\u2013' +
                        u'\u2026' +
                        u'\u0100-\u01f7' +
                        u"\u00c0-\u00ff°«»']")


def sanitize_text(s):
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
        .replace(r"\\'", "'")\
        .replace(r"\'", "'")\
        .replace(u'\xad', '')\
        .replace('<', '&lt;')\
        .replace('>', '&gt;')\
        .replace('\t', ' ')
    for i, c in enumerate(s2):
        if not text_chars.match(c):
            raise ValueError('Unexpected character #%d %r in string "%r"' % (i, c, s2))
    s2 = re.sub(r'\s+', ' ', s2)
    s2 = s2.strip()
    return s2.encode('utf-8')


normalized_grades = {
    u'1Б-2А': '2a',
    u'1Б - 2А': '2a',
    u'1Б-2Б': '2b',
    u'ок.3Б': '3b',
    u'ок.3А': '3a',
    u'1A-1Б': '1b',
    u'1Б-1А': '1b',
    u'н/к*': 'nograde',
    u'н.к.': 'nograde',
    u'ок.2А': '2a',
    u'3Б*': '3b',
    u'3А*': '3a',
    u'1A': '1a',
    u'1Б* (?)': '1b',
    u'2Б(2': '2b',
    u'3А (': '3a',
    u'3A': '3a',
    u'нк': 'nograde',
    u'1А-1Б': '1b',
    u'1A*': '1a',
    u'2Б-3А': '3a',
    u'н к': 'nograde',
    u'1Бтур': '1b',
    u'1Б*': '1b',
    u'2Б*': '2b',
    u'1Блд': '1b',
    u'3А-3Б': '3b',
    u'н/к-1А?': '1a',
    u'1б-2а': '2a',
    u'~2А': '2a',
    u'2Б?': '2b',
    u'1Б?': '1b',
    u'2А-': '2a',
    u'~2A': '2a',
    u'3А,': '3a',
    u'3А*-3Б': '3a',
    u'н/к?': 'nograde',
    u'1A-2А': '2a',
    u'?': 'unknown',
    u'2Б': '2b',
    u'2А': '2a',
    u'2 А': '2a',
    u'~1А': '1a',
    u'2А-3А': '3a',
    u'3А': '3a',
    u'3Б': '3b',
    u'2А-2Б': '2b',
    u'ок.2Б': '2b',
    u'1Бальп': '1a',
    u'2A': '2a',
    u'ок.1Б': '1b',
    u'ок.1А': '1a',
    u'3Б-3Б*': '3b',
    u'1А': '1a',
    u'1Б': '1b',
    u'н.к': 'nograde',
    u'2Б*-3А': '3a',
    u'2б': '2b',
    u'1А*': '1a',
    u'2Аальп': '2a',
    u'н/к': 'nograde',
    u'2А*': '2a',
    u'3а': '3a',
    u'Н/к*': 'nograde',
    u'1А-2А': '2a',
    u'2A*': '2a',
    u'3А-3': '3a',
    u'3Бальп': '3b',
    u'2A-2Б': '2b',
    u'2А - 2Б': '2b',
    u'1А?': '1a',
    u'--': 'unknown',
    u'ос': 'unknown',
    u'н/к-1А': '1a',
    u'1а': '1a',
    u'1б': '1b',
    u'2А?': '2a',
    u'1885': 'unknown',
    u'': 'unknown',
    u'3A альп': '3a',
    u'3Б альп': '3b',
    u'2А альп': '2a',
    u'1А*-1Б': '1b',
}


def norm_grade(grade):
    grade = grade.strip()
    if grade not in normalized_grades:
        raise ValueError('Unknown grade "%s"' % (grade,))
    return normalized_grades[grade]


def check_is_int(s):
    if not s.isdigit():
        raise ValueError('Not digital value "%s"' % (s,))
    return s


def parse_is_summit(tech_type):
    if tech_type == '1':
        return False
    if tech_type == '2':
        return True
    raise ValueError('Unexpected value "%s" for tech_type field' % (tech_type,))


def parse_latitude(lat_str):
    try:
        lat = float(lat_str)
        if not (-90 < lat < 90):
            raise ValueError()
    except ValueError:
        raise ValueError('Invalid latitude "%s"' % (lat_str,))
    return lat


def parse_longitude(lon_str):
    try:
        lon = float(lon_str)
        if not (-180 < lon < 180):
            raise ValueError()
    except ValueError:
        raise ValueError('Invalid longitude "%s"' % (lon_str,))
    return lon


def prepare_comments(raw_comments):
    comments = []
    if not raw_comments:
        return comments
    for raw_c in raw_comments:
        content = sanitize_text(raw_c['title'])
        if not content:
            continue
        comment = {'content': content}
        user = sanitize_text(raw_c.get('user', ''))
        if user:
            comment['user'] = user
        comments.append(comment)
    return comments


def pass_has_coordinates(westra_pass):
    has_lat = bool('latitude' in westra_pass)
    has_lon = bool('longitude' in westra_pass)
    if has_lat != has_lon:
        raise ValueError('Pass id="%s" has only one of latitude and longitude' % westra_pass['id'])
    return has_lat


def get_latlon(westra_pass):
    return [parse_latitude(westra_pass['latitude']), parse_longitude(westra_pass['longitude'])]


def westra_pass_to_nakarte(westra_pass):
    if not pass_has_coordinates(westra_pass):
        return None
    if westra_pass['id'] == '12620': # Test pass
        return None

    try:
        nakarte_pass = {
            'name': sanitize_text(westra_pass['title']),
            'id': check_is_int(westra_pass['id']),
            'altnames': sanitize_text(westra_pass['other_titles']) or None,
            'elevation': check_is_int(westra_pass['height'])
                if (westra_pass['height'] not in ('', '0')) else None,
            'grade': sanitize_text(westra_pass['cat_sum']) or None,
            'grade_eng': norm_grade(westra_pass['cat_sum']),
            'slopes': sanitize_text(westra_pass['type_sum']) or None,
            'connects': sanitize_text(westra_pass['connect']) or None,
            'is_summit': 1 if parse_is_summit(westra_pass['tech_type']) else None,
            'latlon': get_latlon(westra_pass),
            'comments': prepare_comments(westra_pass.get('comments')) or None,
            'author': sanitize_text(westra_pass['user_name']) or None
        }
        if 'reportStat' in westra_pass:
            nakarte_pass['reports_total'] = (check_is_int(westra_pass['reportStat']['total'])
                                             if westra_pass['reportStat']['total'] != '0' else None)
            nakarte_pass['reports_photo']= (check_is_int(westra_pass['reportStat']['photo'])
                                            if westra_pass['reportStat']['photo'] != '0' else None)
            nakarte_pass['reports_tech'] = (check_is_int(westra_pass['reportStat']['tech'])
                                            if westra_pass['reportStat']['tech'] != '0' else None)
    except ValueError as e:
        raise ValueError((u'Invalid pass id="%s": %s' % (westra_pass['id'], e)).encode('utf-8'))
    for k, v in nakarte_pass.items():
        if v is None:
            del nakarte_pass[k]
    return nakarte_pass
