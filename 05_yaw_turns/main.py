#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
ANGLE_DEG = 90.0
RATE_DPS = 60.0


def main() -> None:
    """Take off, perform four quarter turns, then land."""
    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                time.sleep(1.0)
                for index in range(4):
                    log_flight(f"Yaw turn {index + 1}/4: left {ANGLE_DEG:.0f} deg [...]")
                    mc.turn_left(ANGLE_DEG, rate=RATE_DPS)
                    time.sleep(0.5)
            log_flight("Yaw sequence completed and landing completed.")


if __name__ == "__main__":
    run_demo(main)