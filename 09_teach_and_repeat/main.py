#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from cflib.positioning.motion_commander import MotionCommander

from utils.path_tools import (
    path_length,
    path_segments,
    prepare_learned_path,
    record_xy_path,
    reset_position_estimator,
)
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

RECORD_SECONDS = 8.0
HEIGHT_M = 0.40
VELOCITY_MPS = 0.15
MIN_TAUGHT_PATH_M = 0.15


def log_learning(message: str) -> None:
    """Print a consistently formatted learning message."""
    print(f"[learning]\t{message}")


def _confirm_replay() -> bool:
    response = input("Replay the learned path now? [y/N]: ").strip().lower()
    return response in {"y", "yes"}


def main() -> None:
    """Record a hand-taught path, simplify it, and optionally replay it."""
    with preflight_connection(require_flow_deck=True) as scf:
        log_learning("Teaching mode: motors remain off.")
        log_learning("Keep the Crazyflie front pointing in one fixed direction.")
        log_learning("Move it slowly 10-25 cm above a textured floor.")
        input("Press ENTER when the drone is stationary and you are ready: ")

        log_learning("Resetting position estimator [...]")
        reset_position_estimator(scf)

        log_learning(f"Recording for {RECORD_SECONDS:.1f} s [...]")
        raw_path = record_xy_path(scf, duration_s=RECORD_SECONDS)
        learned_path, scale = prepare_learned_path(raw_path)

        learned_length = path_length(learned_path)
        segments = path_segments(learned_path)

        if learned_length < MIN_TAUGHT_PATH_M or not segments:
            raise RuntimeError(
                "The taught path is too short. Move the Crazyflie farther and try again."
            )

        log_learning(f"Raw samples: {len(raw_path)}")
        log_learning(f"Simplified points: {len(learned_path)}")
        log_learning(f"Replay segments: {len(segments)}")
        log_learning(f"Replay path length: {learned_length:.2f} m")
        if scale < 0.999:
            log_learning(f"Safety scaling applied: {scale * 100:.0f} %")

        print()
        log_learning("Return the Crazyflie to the launch point.")
        log_learning("Keep the same front direction used while teaching.")
        log_learning("Place it flat on the floor and do not touch it before takeoff.")

        if not _confirm_replay():
            log_learning("Replay cancelled. Learned path was not flown.")
            return

        with armed(scf):
            log_flight(f"Taking off to about {HEIGHT_M:.2f} m [...]")
            with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                time.sleep(1.0)
                log_flight(f"Replaying {len(segments)} learned segments [...]")
                for index, (dx, dy) in enumerate(segments, start=1):
                    log_flight(
                        f"Segment {index}/{len(segments)}: "
                        f"dx={dx:+.2f} m, dy={dy:+.2f} m"
                    )
                    mc.move_distance(dx, dy, 0.0, velocity=VELOCITY_MPS)
                    time.sleep(0.10)
                time.sleep(1.0)
            log_flight("Landing completed.")


if __name__ == "__main__":
    run_demo(main)