import math
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import shapely
import shapely.ops
from scipy.spatial.qhull import Delaunay  # type: ignore

from .webmercator import web_mercator_to_wgs84, wgs84_to_web_mercator

CONCAVE_ALPHA_METERS = 20000
BUFFER_METERS = 1000
SIMPLIFY_METERS = 1000


def alpha_shape(
    points: list[tuple[float, float]], alpha: float
) -> shapely.geometry.base.BaseGeometry:
    """
    Compute the alpha shape (concave hull) of a set
    of points.
    @param points: Iterable container of points.
    @param alpha: alpha value to influence the
        gooeyness of the border. Smaller numbers
        don't fall inward as much as larger numbers.
        Too large, and you lose everything!
    """
    if len(points) < 4:
        # When you have a triangle, there is no sense
        # in computing an alpha shape.
        return shapely.geometry.MultiPoint(list(points)).convex_hull

    def add_edge(
        edges: set[tuple[float, float]],
        edge_points: list[npt.NDArray[np.float64]],
        coords: npt.NDArray[np.float64],
        i: int,
        j: int,
    ) -> None:
        """
        Add a line between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            return
        edges.add((i, j))
        edge_points.append(coords[[i, j]])

    coords: npt.NDArray[np.float64] = np.array(points)
    tri = Delaunay(coords)
    edges: set[tuple[float, float]] = set()
    edge_points: list[npt.NDArray[np.float64]] = []
    # loop over triangles:
    # ia, ib, ic = indices of corner points of the
    # triangle
    for ia, ib, ic in tri.vertices:
        pa = coords[ia]
        pb = coords[ib]
        pc = coords[ic]
        # Lengths of sides of triangle
        a = math.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = math.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = math.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)
        # Semiperimeter of triangle
        s = (a + b + c) / 2.0
        # Area of triangle by Heron's formula
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        circum_r = a * b * c / (4.0 * area)
        # Here's the radius filter.
        # print circum_r
        if circum_r < 1.0 / alpha:
            add_edge(edges, edge_points, coords, ia, ib)
            add_edge(edges, edge_points, coords, ib, ic)
            add_edge(edges, edge_points, coords, ic, ia)
    m = shapely.geometry.MultiLineString(edge_points)
    triangles = list(shapely.ops.polygonize(m))
    return shapely.ops.cascaded_union(triangles)


def make_coverage_geojson(points: list[tuple[float, float]]) -> Any:
    points_projected = [wgs84_to_web_mercator(*point) for point in points]
    coverage = alpha_shape(points_projected, 1.0 / CONCAVE_ALPHA_METERS)
    coverage = coverage.buffer(BUFFER_METERS)
    coverage = coverage.simplify(SIMPLIFY_METERS)
    assert coverage.geom_type == "MultiPolygon"
    coverage = cast(shapely.geometry.MultiPolygon, coverage)

    single_points = shapely.geometry.MultiPoint(points_projected).difference(coverage)
    single_points_coverage = cast(
        shapely.geometry.MultiPolygon, single_points.buffer(1)
    )
    assert single_points_coverage.geom_type == "MultiPolygon"
    coverage = shapely.geometry.MultiPolygon(
        list(coverage.geoms) + list(single_points_coverage.geoms)
    )
    coverage = shapely.ops.transform(web_mercator_to_wgs84, coverage)  # type: ignore[arg-type]
    return coverage.__geo_interface__
