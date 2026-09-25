#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.telemetry import log_stream, log_telemetry
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
STEP_M = 0.80


def main() -> None:
    """Fly a short vertical profile while streaming height telemetry."""
    def on_data(_timestamp, data, _log_conf) -> None:
        range_m = float(data["range.zrange"]) / 1000.0
        estimate_m = float(data["stateEstimate.z"])
        log_telemetry(f"range={range_m:.3f} m  estimate_z={estimate_m:.3f} m")

    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with log_stream(
                scf,
                name="HeightSweep",
                variables=["range.zrange", "stateEstimate.z"],
                period_ms=150,
                callback=on_data,
            ):
                with MotionCommander(scf, default_height=HEIGHT_M) as mc:
                    time.sleep(1.0)
                    for _ in range(2):
                        log_flight(f"Climbing {STEP_M:.2f} m [...]")
                        mc.up(STEP_M, velocity=0.10)
                        time.sleep(1.0)
                    for _ in range(2):
                        log_flight(f"Descending {STEP_M:.2f} m [...]")
                        mc.down(STEP_M, velocity=0.10)
                        time.sleep(1.0)
            log_flight("Height sweep completed and landing completed.")


if __name__ == "__main__":
    run_demo(main)
