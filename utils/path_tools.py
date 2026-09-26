#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Path recording, simplification, safety fitting, and shape classification helpers."""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass
from typing import Iterable

from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from utils.telemetry import collect_log_samples

Point2D = tuple[float, float]


@dataclass(frozen=True)
class ShapeResult:
    """Result returned by the geometric shape classifier."""

    name: str
    confidence: int
    metrics: dict[str, float]


def reset_position_estimator(scf: SyncCrazyflie, settle_s: float = 2.0) -> None:
    """Reset the Crazyflie Kalman estimator and wait for it to settle."""
    scf.cf.param.set_value("kalman.resetEstimation", "1")
    time.sleep(0.1)
    scf.cf.param.set_value("kalman.resetEstimation", "0")
    time.sleep(settle_s)


def record_xy_path(
    scf: SyncCrazyflie,
    *,
    duration_s: float,
    period_ms: int = 50,
) -> list[Point2D]:
    """Record the estimated XY path for a fixed duration."""
    samples = collect_log_samples(
        scf,
        ["stateEstimate.x", "stateEstimate.y"],
        duration_s=duration_s,
        period_ms=period_ms,
        name="LearnedPath",
    )

    points: list[Point2D] = []
    for _timestamp, data in samples:
        if "stateEstimate.x" in data and "stateEstimate.y" in data:
            points.append(
                (float(data["stateEstimate.x"]), float(data["stateEstimate.y"]))
            )

    if not points:
        return []

    start_x, start_y = points[0]
    return [(x - start_x, y - start_y) for x, y in points]


def path_length(points: Iterable[Point2D]) -> float:
    """Return the total polyline length in meters."""
    items = list(points)
    return sum(math.dist(a, b) for a, b in zip(items, items[1:]))


def endpoint_distance(points: list[Point2D]) -> float:
    """Return the distance between the first and last path samples."""
    if len(points) < 2:
        return 0.0
    return math.dist(points[0], points[-1])


def bounding_box(points: list[Point2D]) -> tuple[float, float, float, float]:
    """Return min_x, max_x, min_y, max_y for a path."""
    if not points:
        return 0.0, 0.0, 0.0, 0.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), max(xs), min(ys), max(ys)


def smooth_path(points: list[Point2D], window: int = 5) -> list[Point2D]:
    """Apply a small moving-average filter while preserving path length."""
    if window <= 1 or len(points) < window:
        return list(points)

    half = window // 2
    smoothed: list[Point2D] = []
    for index in range(len(points)):
        start = max(0, index - half)
        stop = min(len(points), index + half + 1)
        chunk = points[start:stop]
        smoothed.append(
            (
                sum(point[0] for point in chunk) / len(chunk),
                sum(point[1] for point in chunk) / len(chunk),
            )
        )
    return smoothed


def remove_near_duplicates(
    points: list[Point2D],
    *,
    min_distance_m: float = 0.008,
) -> list[Point2D]:
    """Remove samples that are too close to the previously retained point."""
    if not points:
        return []

    filtered = [points[0]]
    for point in points[1:]:
        if math.dist(filtered[-1], point) >= min_distance_m:
            filtered.append(point)

    if len(filtered) == 1 and len(points) > 1:
        filtered.append(points[-1])
    return filtered


def _distance_to_segment(point: Point2D, start: Point2D, end: Point2D) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0.0 and dy == 0.0:
        return math.dist(point, start)

    t = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dy
    ) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projection = (start[0] + t * dx, start[1] + t * dy)
    return math.dist(point, projection)


def simplify_path(points: list[Point2D], epsilon_m: float = 0.025) -> list[Point2D]:
    """Simplify a path using the Ramer-Douglas-Peucker algorithm."""
    if len(points) <= 2:
        return list(points)

    start = points[0]
    end = points[-1]
    max_distance = -1.0
    split_index = 0

    for index, point in enumerate(points[1:-1], start=1):
        distance = _distance_to_segment(point, start, end)
        if distance > max_distance:
            max_distance = distance
            split_index = index

    if max_distance > epsilon_m:
        left = simplify_path(points[: split_index + 1], epsilon_m)
        right = simplify_path(points[split_index:], epsilon_m)
        return left[:-1] + right

    return [start, end]


def simplify_to_max_points(
    points: list[Point2D],
    *,
    max_points: int = 16,
    initial_epsilon_m: float = 0.02,
) -> list[Point2D]:
    """Increase simplification tolerance until the path fits a point budget."""
    if len(points) <= max_points:
        return list(points)

    epsilon = initial_epsilon_m
    simplified = simplify_path(points, epsilon)
    while len(simplified) > max_points and epsilon < 0.20:
        epsilon *= 1.35
        simplified = simplify_path(points, epsilon)
    return simplified


def fit_path_to_limits(
    points: list[Point2D],
    *,
    max_span_m: float = 0.55,
    max_length_m: float = 1.50,
) -> tuple[list[Point2D], float]:
    """Uniformly scale a learned path so it fits conservative flight limits."""
    if not points:
        return [], 1.0

    min_x, max_x, min_y, max_y = bounding_box(points)
    span = max(max_x - min_x, max_y - min_y)
    length = path_length(points)

    scale = 1.0
    if span > max_span_m and span > 0.0:
        scale = min(scale, max_span_m / span)
    if length > max_length_m and length > 0.0:
        scale = min(scale, max_length_m / length)

    return [(x * scale, y * scale) for x, y in points], scale


def path_segments(
    points: list[Point2D],
    *,
    min_segment_m: float = 0.02,
) -> list[Point2D]:
    """Convert absolute path points into relative XY motion segments."""
    segments: list[Point2D] = []
    for start, end in zip(points, points[1:]):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        if math.hypot(dx, dy) >= min_segment_m:
            segments.append((dx, dy))
    return segments


def prepare_learned_path(
    raw_points: list[Point2D],
    *,
    max_points: int = 16,
) -> tuple[list[Point2D], float]:
    """Filter, simplify, and safety-scale a manually taught path."""
    filtered = remove_near_duplicates(smooth_path(raw_points, window=5))
    simplified = simplify_to_max_points(filtered, max_points=max_points)
    return fit_path_to_limits(simplified)


def _mean_distance_to_box_edges(points: list[Point2D]) -> float:
    min_x, max_x, min_y, max_y = bounding_box(points)
    width = max_x - min_x
    height = max_y - min_y
    scale = max(width, height, 1e-6)

    distances = []
    for x, y in points:
        distances.append(
            min(
                abs(x - min_x),
                abs(x - max_x),
                abs(y - min_y),
                abs(y - max_y),
            )
            / scale
        )
    return sum(distances) / len(distances)


def classify_shape(points: list[Point2D]) -> ShapeResult:
    """Classify a hand-drawn path as LINE, SQUARE, CIRCLE, or UNKNOWN.

    This is a deterministic geometric classifier, not a machine-learning model.
    """
    processed = remove_near_duplicates(smooth_path(points, window=5))
    length = path_length(processed)
    if len(processed) < 5 or length < 0.12:
        return ShapeResult("UNKNOWN", 0, {"path_length_m": length})

    end_distance = endpoint_distance(processed)
    straightness = min(1.0, end_distance / max(length, 1e-6))

    min_x, max_x, min_y, max_y = bounding_box(processed)
    width = max_x - min_x
    height = max_y - min_y
    span = max(width, height, 1e-6)
    aspect = min(width, height) / span
    closure = end_distance / max(length, 1e-6)

    center_x = sum(point[0] for point in processed) / len(processed)
    center_y = sum(point[1] for point in processed) / len(processed)
    radii = [math.hypot(x - center_x, y - center_y) for x, y in processed]
    mean_radius = statistics.fmean(radii)
    radial_cv = (
        statistics.pstdev(radii) / mean_radius if mean_radius > 1e-6 else 1.0
    )

    box_edge_error = _mean_distance_to_box_edges(processed)

    metrics = {
        "path_length_m": length,
        "closure": closure,
        "straightness": straightness,
        "aspect": aspect,
        "radial_cv": radial_cv,
        "box_edge_error": box_edge_error,
    }

    if straightness >= 0.82 and end_distance >= 0.12:
        confidence = int(max(0.0, min(1.0, (straightness - 0.72) / 0.28)) * 100)
        return ShapeResult("LINE", confidence, metrics)

    if closure > 0.28 or aspect < 0.45:
        return ShapeResult("UNKNOWN", 25, metrics)

    closure_score = max(0.0, min(1.0, 1.0 - closure / 0.28))
    aspect_score = max(0.0, min(1.0, (aspect - 0.45) / 0.55))
    circle_radius_score = max(0.0, min(1.0, 1.0 - radial_cv / 0.38))
    square_edge_score = max(0.0, min(1.0, 1.0 - box_edge_error / 0.18))

    circle_score = 0.35 * closure_score + 0.25 * aspect_score + 0.40 * circle_radius_score
    square_score = 0.35 * closure_score + 0.25 * aspect_score + 0.40 * square_edge_score

    if circle_score < 0.56 and square_score < 0.56:
        return ShapeResult("UNKNOWN", int(max(circle_score, square_score) * 100), metrics)

    if circle_score >= square_score:
        return ShapeResult("CIRCLE", int(min(0.99, circle_score) * 100), metrics)
    return ShapeResult("SQUARE", int(min(0.99, square_score) * 100), metrics)
