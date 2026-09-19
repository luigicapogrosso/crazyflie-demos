#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
LONG_SIDE_M = 0.70
SHORT_SIDE_M = 0.30
VELOCITY_MPS = 0.20


def main() -> None:
    """Take off, fly a rectangle, then land."""
    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                time.sleep(1.0)
                legs = (
                    ("Forward", mc.forward, LONG_SIDE_M),
                    ("Right", mc.right, SHORT_SIDE_M),
                    ("Back", mc.back, LONG_SIDE_M),
                    ("Left", mc.left, SHORT_SIDE_M),
                )
                for label, move, distance in legs:
                    log_flight(f"{label} {distance:.2f} m [...]")
                    move(distance, velocity=VELOCITY_MPS)
                    time.sleep(0.4)
            log_flight("Rectangle completed and landing completed.")


if __name__ == "__main__":
    run_demo(main)