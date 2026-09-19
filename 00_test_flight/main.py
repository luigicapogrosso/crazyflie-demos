#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from cflib.positioning.motion_commander import MotionCommander

from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
HOVER_SECONDS = 3.0


def main() -> None:
    """Arm, take off, hover briefly, land and disarm."""
    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            log_flight(f"Taking off to about {HEIGHT_M:.2f} m [...]")
            with MotionCommander(scf, default_height=HEIGHT_M):
                log_flight(f"Hovering for {HOVER_SECONDS:.1f} s [...]")
                time.sleep(HOVER_SECONDS)
            log_flight("Landing completed.")


if __name__ == "__main__":
    run_demo(main)