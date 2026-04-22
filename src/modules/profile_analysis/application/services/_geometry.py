import math

_METERS_PER_DEGREE_LAT: float = 111_320.0
_FULL_CIRCLE_DEG: float = 360.0
_ITER_EPSILON_FACTOR: float = 1e-9


def normalize_angle(angle_deg: float) -> float:
    return angle_deg % _FULL_CIRCLE_DEG


def circular_window(start_deg: float, end_deg: float) -> tuple[float, float]:
    start = normalize_angle(start_deg)
    end = normalize_angle(end_deg)
    if end <= start:
        end += _FULL_CIRCLE_DEG
    return start, end


def degrees_for_arc_step(radius_m: float, step_m: float) -> float:
    if radius_m <= 0:
        return _FULL_CIRCLE_DEG
    return math.degrees(step_m / radius_m)


def iter_linear_space(start: float, end: float, step: float, include_end: bool) -> list[float]:
    if step <= 0:
        raise ValueError("step must be positive")

    epsilon = step * _ITER_EPSILON_FACTOR
    values: list[float] = []
    cursor = start
    while cursor < end - epsilon:
        values.append(cursor)
        cursor += step

    if include_end and (not values or abs(values[-1] - end) > epsilon):
        values.append(end)

    return values


def insert_anchors(values: list[float], anchors: list[float], step: float) -> list[float]:
    """Return *values* with any *anchors* not already covered inserted and sorted.

    A grid value is considered to "cover" an anchor when they are within
    ``step * 0.5`` of each other, which handles normal floating-point drift
    from accumulated additions.
    """
    epsilon = step * 0.5
    extra = [a for a in anchors if not any(abs(v - a) <= epsilon for v in values)]
    return sorted(values + extra)


def polar_to_lon_lat(
    center_lon: float,
    center_lat: float,
    radius_m: float,
    azimuth_deg: float,
) -> tuple[float, float]:
    lat_rad = math.radians(center_lat)
    meters_per_degree_lon = max(1e-9, _METERS_PER_DEGREE_LAT * math.cos(lat_rad))

    azimuth_rad = math.radians(azimuth_deg)
    delta_x = radius_m * math.sin(azimuth_rad)
    delta_y = radius_m * math.cos(azimuth_rad)

    lon = center_lon + (delta_x / meters_per_degree_lon)
    lat = center_lat + (delta_y / _METERS_PER_DEGREE_LAT)
    return lon, lat
