#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from cflib.positioning.motion_commander import MotionCommander

from utils.path_tools import classify_shape, record_xy_path, reset_position_estimator
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

RECORD_SECONDS = 8.0
HEIGHT_M = 0.30
VELOCITY_MPS = 0.15
SQUARE_SIDE_M = 0.25
CIRCLE_RADIUS_M = 0.16
LINE_DISTANCE_M = 0.30


def log_analysis(message: str) -> None:
    """Print a consistently formatted analysis message."""
    print(f"[analysis]\t{message}")


def _confirm_flight(shape: str) -> bool:
    response = input(f"Fly a small {shape.lower()} now? [y/N]: ").strip().lower()
    return response in {"y", "yes"}


def _fly_shape(mc: MotionCommander, shape: str) -> None:
    if shape == "LINE":
        mc.forward(LINE_DISTANCE_M, velocity=VELOCITY_MPS)
        mc.back(LINE_DISTANCE_M, velocity=VELOCITY_MPS)
        return

    if shape == "SQUARE":
        mc.forward(SQUARE_SIDE_M, velocity=VELOCITY_MPS)
        mc.right(SQUARE_SIDE_M, velocity=VELOCITY_MPS)
        mc.back(SQUARE_SIDE_M, velocity=VELOCITY_MPS)
        mc.left(SQUARE_SIDE_M, velocity=VELOCITY_MPS)
        return

    if shape == "CIRCLE":
        mc.circle_left(CIRCLE_RADIUS_M, velocity=VELOCITY_MPS)
        return

    raise ValueError(f"Unsupported shape: {shape}")


def main() -> None:
    """Record a hand-drawn path, classify it, and optionally fly the result."""
    with preflight_connection(require_flow_deck=True) as scf:
        log_analysis("Recognition mode: motors remain off while you draw.")
        log_analysis("Draw one shape: LINE, SQUARE, or CIRCLE.")
        log_analysis("Keep the drone front pointing in one fixed direction.")
        log_analysis("Move slowly 10-25 cm above a textured floor.")
        input("Press ENTER when the drone is stationary and you are ready: ")

        log_analysis("Resetting position estimator [...]")
        reset_position_estimator(scf)
        log_analysis(f"Recording for {RECORD_SECONDS:.1f} s [...]")
        path = record_xy_path(scf, duration_s=RECORD_SECONDS)

        result = classify_shape(path)
        log_analysis(f"Samples collected: {len(path)}")
        log_analysis(f"Shape detected: {result.name}")
        log_analysis(f"Confidence: {result.confidence} %")

        if result.metrics:
            log_analysis(
                "Metrics: "
                f"closure={result.metrics.get('closure', 0.0):.2f}, "
                f"straightness={result.metrics.get('straightness', 0.0):.2f}, "
                f"aspect={result.metrics.get('aspect', 0.0):.2f}"
            )

        if result.name == "UNKNOWN":
            log_analysis("No flight: draw a clearer line, square, or circle and retry.")
            return

        print()
        log_analysis("Place the Crazyflie flat at the launch point.")
        log_analysis("Keep the flight area clear before confirming.")

        if not _confirm_flight(result.name):
            log_analysis("Flight cancelled. Recognition completed successfully.")
            return

        with armed(scf):
            log_flight(f"Taking off to about {HEIGHT_M:.2f} m [...]")
            with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                time.sleep(1.0)
                log_flight(f"Flying recognized shape: {result.name} [...]")
                _fly_shape(mc, result.name)
                time.sleep(1.0)
            log_flight("Landing completed.")


if __name__ == "__main__":
    run_demo(main)