"""Geographic helpers."""
from math import asin, cos, degrees, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in kilometres."""
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, list[tuple[float, float]]]:
    """Return (min_lat, max_lat, longitude_ranges) enclosing the search circle.

    A cheap rectangle used to narrow the SQL query before the exact haversine
    check. Longitude ranges are within [-180, 180]; a box crossing the
    antimeridian yields two ranges. Near a pole, or for very large radii,
    every longitude is included.
    """
    dlat = degrees(radius_km / EARTH_RADIUS_KM)
    min_lat, max_lat = max(lat - dlat, -90.0), min(lat + dlat, 90.0)
    if max_lat >= 90.0 or min_lat <= -90.0:
        return min_lat, max_lat, [(-180.0, 180.0)]
    dlon = degrees(radius_km / (EARTH_RADIUS_KM * cos(radians(min(abs(lat) + dlat, 89.999)))))
    if dlon >= 180.0:
        return min_lat, max_lat, [(-180.0, 180.0)]
    low, high = lon - dlon, lon + dlon
    if low < -180.0:
        return min_lat, max_lat, [(low + 360.0, 180.0), (-180.0, high)]
    if high > 180.0:
        return min_lat, max_lat, [(low, 180.0), (-180.0, high - 360.0)]
    return min_lat, max_lat, [(low, high)]
