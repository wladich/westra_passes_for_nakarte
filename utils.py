# coding: utf-8
import json


def write_json_with_float_precision(data, fd, precision, **kwargs):
    orig_float_repr = json.encoder.FLOAT_REPR
    format_str = '.{}f'.format(precision)
    json.encoder.FLOAT_REPR = lambda x: format(x, format_str)
    try:
        json.dump(data, fd, indent=None, **kwargs)
    finally:
        json.encoder.FLOAT_REPR = orig_float_repr
