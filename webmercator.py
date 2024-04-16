# coding: utf-8

import math

R = 20037508.34


def wgs84_to_web_mercator(lon, lat):
    x = lon * R / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * R / 180
    return x, y


def web_mercator_to_wgs84(x, y):
    lon = (x / R) * 180
    lat = (y / R) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lon, lat


if __name__ == "__main__":
    import unittest

    class TestCoordinateConversion(unittest.TestCase):
        def test_wgs84_to_web_mercator(self):
            # Test with known WGS84 coordinates
            wgs_lon, wgs_lat = 37.6175, 55.7522
            mercator_x, mercator_y = wgs84_to_web_mercator(wgs_lon, wgs_lat)
            # Expected Web Mercator coordinates
            expected_mercator_x, expected_mercator_y = (
                4187560.9449159685,
                7509243.01057922,
            )
            # Check if the calculated values are close to expected values
            self.assertAlmostEqual(mercator_x, expected_mercator_x, delta=0.1)
            self.assertAlmostEqual(mercator_y, expected_mercator_y, delta=0.1)

        def test_web_mercator_to_wgs84(self):
            # Test with known Web Mercator coordinates
            mercator_x, mercator_y = 4187560.9449159685, 7509243.01057922
            wgs_lon, wgs_lat = web_mercator_to_wgs84(mercator_x, mercator_y)
            # Expected WGS84 coordinates
            expected_wgs_lon = 37.6175
            expected_wgs_lat = 55.7522
            # Check if the calculated values are close to expected values
            self.assertAlmostEqual(wgs_lon, expected_wgs_lon, delta=0.000001)
            self.assertAlmostEqual(wgs_lat, expected_wgs_lat, delta=0.000001)

    unittest.main()
