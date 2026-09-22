#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.telemetry import log_stream
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
HOVER_SECONDS = 10.0


def main() -> None:
    """Hover briefly and report observed battery-voltage range."""
    samples: list[float] = []

    def on_data(_timestamp, data, _log_conf) -> None:
        samples.append(float(data["pm.vbat"]))

    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with log_stream(scf, name="BatterySag", variables=["pm.vbat"], period_ms=100, callback=on_data):
                with MotionCommander(scf, default_height=HEIGHT_M):
                    log_flight(f"Hovering for {HOVER_SECONDS:.1f} s while measuring battery [...]")
                    time.sleep(HOVER_SECONDS)
            log_flight("Landing completed.")

    if samples:
        maximum = max(samples)
        minimum = min(samples)
        log_flight(f"Battery maximum during test: {maximum:.2f} V")
        log_flight(f"Battery minimum during test: {minimum:.2f} V")
        log_flight(f"Observed voltage range: {maximum - minimum:.2f} V")


if __name__ == "__main__":
    run_demo(main)