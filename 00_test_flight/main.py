#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Demo 00 - Test flight.

Run the shared pre-flight checks, verify the Flow Deck V2, explicitly arm the
Crazyflie, take off to about 30 cm, hover for 3 seconds, then land and disarm.

This is intentionally the smallest flight demo in the repository. Use it
before more complex trajectories to verify that the radio link, Flow Deck,
position estimate, motors and propellers behave as expected.
"""

import sys
import time

from cflib.positioning.motion_commander import MotionCommander

from utils.toolbox import (
    PreflightError,
    armed,
    log_flight,
    log_preflight,
    preflight_connection,
)


HEIGHT_M = 0.30
HOVER_SECONDS = 3.0


def main() -> None:
    """Arm, take off, hover briefly, land and disarm after pre-flight checks."""
    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            log_flight(f"Taking off to about {HEIGHT_M:.2f} m [...]")

            with MotionCommander(scf, default_height=HEIGHT_M):
                log_flight(f"Hovering for {HOVER_SECONDS:.1f} s [...]")
                time.sleep(HOVER_SECONDS)

            log_flight("Landing completed.")


if __name__ == "__main__":
    try:
        main()
    except PreflightError as exc:
        print()
        log_preflight(f"FAILED: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        log_flight("Interrupted by user.")
        sys.exit(130)