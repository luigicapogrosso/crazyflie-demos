#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
SIDE_M = 0.35
VELOCITY_MPS = 0.20


def main() -> None:
    """Take off, fly a square, then land."""
    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                time.sleep(1.0)
                for label, move in (
                    ("Forward", mc.forward),
                    ("Right", mc.right),
                    ("Back", mc.back),
                    ("Left", mc.left),
                ):
                    log_flight(f"{label} {SIDE_M:.2f} m [...]")
                    move(SIDE_M, velocity=VELOCITY_MPS)
                    time.sleep(0.4)
            log_flight("Square completed and landing completed.")


if __name__ == "__main__":
    run_demo(main)