"""Demo 11 - Stream position, yaw and battery telemetry during a hover."""

import time
from cflib.positioning.motion_commander import MotionCommander
from utils.telemetry import log_stream, log_telemetry
from utils.toolbox import armed, log_flight, preflight_connection, run_demo

HEIGHT_M = 0.30
HOVER_SECONDS = 10.0
VARIABLES = [
    "stateEstimate.x",
    "stateEstimate.y",
    "stateEstimate.z",
    "stabilizer.yaw",
    "pm.vbat",
]


def main() -> None:
    """Hover while printing live flight telemetry."""
    def on_data(_timestamp, data, _log_conf) -> None:
        log_telemetry(
            f"x={data['stateEstimate.x']:+.3f} m  "
            f"y={data['stateEstimate.y']:+.3f} m  "
            f"z={data['stateEstimate.z']:+.3f} m  "
            f"yaw={data['stabilizer.yaw']:+.1f} deg  "
            f"vbat={data['pm.vbat']:.2f} V"
        )

    with preflight_connection(require_flow_deck=True) as scf:
        with armed(scf):
            with log_stream(scf, name="FlightData", variables=VARIABLES, period_ms=200, callback=on_data):
                with MotionCommander(scf, default_height=HEIGHT_M):
                    log_flight(f"Hovering for {HOVER_SECONDS:.1f} s with telemetry [...]")
                    time.sleep(HOVER_SECONDS)
            log_flight("Landing completed.")


if __name__ == "__main__":
    run_demo(main)