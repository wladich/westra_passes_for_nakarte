# coding: utf-8
import json
from typing import Any, TextIO


def round_floats(data: Any, precision: int) -> Any:
    if isinstance(data, float):
        return round(data, precision)
    if isinstance(data, dict):
        return {k: round_floats(v, precision) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [round_floats(x, precision) for x in data]
    return data


def write_json_with_float_precision(
    data: Any, fd: TextIO, precision: int, **kwargs: Any
) -> None:
    json.dump(round_floats(data, precision), fd, indent=None, **kwargs)
