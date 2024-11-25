# coding: utf-8
import json
from typing import Any, TextIO

PRECISION = 5


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


def write_json_file_with_fixed_precision(filename: str, data: Any) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        write_json_with_float_precision(data, f, precision=5, ensure_ascii=False)
