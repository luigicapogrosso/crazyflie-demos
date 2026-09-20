#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
RADIUS_M = 0.45
VELOCITY_MPS = 0.15


def main() -> None:
    """Take off, fly two opposite circles, then land."""
    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                time.sleep(1.0)
                log_flight("Counter-clockwise loop [...]")
                mc.circle_left(RADIUS_M, velocity=VELOCITY_MPS, angle_degrees=360.0)
                time.sleep(0.5)
                log_flight("Clockwise loop [...]")
                mc.circle_right(RADIUS_M, velocity=VELOCITY_MPS, angle_degrees=360.0)
                time.sleep(0.8)
            log_flight("Figure eight completed and landing completed.")


if __name__ == "__main__":
    run_demo(main)