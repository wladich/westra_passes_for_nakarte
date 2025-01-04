# coding: utf-8
from mountain_passes_for_nakarte.fstr.catalogueparser import (
    normalize_coordinates_cell,
    CoordinatesWithPrecision,
)
import pytest


@pytest.mark.parametrize(
    "cell_text,expected_coords",
    [
        (
            "N 41°59.199'\nE 76°35.068'",
            {
                "": CoordinatesWithPrecision(
                    latitude=41.98665, longitude=76.58446666666667, exact=True
                )
            },
        )
    ],
)
def test_normalize_coordinates_cell(cell_text, expected_coords):
    result = normalize_coordinates_cell(cell_text, True)
    assert result == (expected_coords, None)
