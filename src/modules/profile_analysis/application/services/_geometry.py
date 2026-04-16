import math


def normalize_angle(angle_deg: float) -> float:
    return angle_deg % 360.0


def circular_window(start_deg: float, end_deg: float) -> tuple[float, float]:
    start = normalize_angle(start_deg)
    end = normalize_angle(end_deg)
    if end <= start:
        end += 360.0
    return start, end


def degrees_for_arc_step(radius_m: float, step_m: float) -> float:
    if radius_m <= 0:
        return 360.0
    return math.degrees(step_m / radius_m)


def iter_linear_space(start: float, end: float, step: float, include_end: bool) -> list[float]:
    if step <= 0:
        raise ValueError("step must be positive")

    values: list[float] = []
    cursor = start
    epsilon = step * 1e-9
    while cursor < end - epsilon:
        values.append(cursor)
        cursor += step

    if include_end:
        if not values or abs(values[-1] - end) > epsilon:
            values.append(end)

    return values


def polar_to_lon_lat(center_lon: float, center_lat: float, radius_m: float, azimuth_deg: float) -> tuple[float, float]:
    lat_rad = math.radians(center_lat)
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = max(1e-9, meters_per_degree_lat * math.cos(lat_rad))

    azimuth_rad = math.radians(azimuth_deg)
    delta_x = radius_m * math.sin(azimuth_rad)
    delta_y = radius_m * math.cos(azimuth_rad)

    lon = center_lon + (delta_x / meters_per_degree_lon)
    lat = center_lat + (delta_y / meters_per_degree_lat)
    return lon, lat
