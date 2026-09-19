#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared utilities for Crazyflie connection and pre-flight checks.

This module centralizes the checks that should run before every flight demo,
so numbered demo modules can stay focused on demo-specific behavior.
"""

from __future__ import annotations

import logging
import os
import time
import warnings
from contextlib import contextmanager
from threading import Event
from typing import Iterator

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


DEFAULT_BATTERY_WARNING_V = 3.70
DEFAULT_MIN_BATTERY_V = 3.60

_drivers_initialized = False


class PreflightError(RuntimeError):
    """Raised when a condition prevents the demo from flying safely."""


def log_preflight(message: str) -> None:
    """Print a consistently formatted pre-flight log message."""
    print(f"[preflight]\t{message}")


def log_flight(message: str) -> None:
    """Print a consistently formatted flight log message."""
    print(f"[flight]\t{message}")


def _configure_cflib_output() -> None:
    """Keep cflib compatibility fallbacks from flooding demo output.

    The project intentionally does not persist the cflib TOC cache. Current
    cflib versions log a warning whenever a TOC cannot be written, even though
    running without a cache is supported. Hide that logger only.

    Older Crazyflie firmware uses legacy commander packet formats. cflib
    transparently falls back to those formats but emits a warning for every
    setpoint. Hide the repeated warnings and report compatibility mode once in
    the pre-flight output instead.
    """
    logging.getLogger("cflib.crazyflie.toccache").setLevel(logging.ERROR)

    warnings.filterwarnings(
        "ignore",
        message=(
            r"Using legacy TYPE_(?:HOVER|ZDISTANCE|VELOCITY_WORLD)_LEGACY\. "
            r"Please update your crazyflie-firmware\."
        ),
        category=DeprecationWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=(
            r"The supervisor subsystem requires CRTP protocol version 12 or later\. "
            r".*Using legacy fallback\."
        ),
        category=UserWarning,
    )


def init_drivers() -> None:
    """Initialize the CRTP drivers once per process."""
    global _drivers_initialized

    if not _drivers_initialized:
        _configure_cflib_output()
        cflib.crtp.init_drivers()
        _drivers_initialized = True


def scan_crazyflies() -> list[str]:
    """Return the Crazyflie URIs found on the available interfaces."""
    init_drivers()

    interfaces = cflib.crtp.scan_interfaces()
    uris: list[str] = []

    for interface in interfaces:
        if interface:
            uris.append(str(interface[0]))

    return uris


def resolve_uri(uri: str | None = None) -> str:
    """Resolve the radio URI to use.

    Priority:
    1. explicit ``uri`` argument;
    2. ``CF_URI`` environment variable;
    3. automatic radio scan.

    If more than one radio device is found, ``CF_URI`` must be set explicitly
    to avoid controlling the wrong Crazyflie.
    """
    explicit_uri = uri or os.environ.get("CF_URI")

    if explicit_uri:
        if not explicit_uri.startswith("radio://"):
            raise PreflightError(
                f"Invalid flight URI: {explicit_uri!r}. "
                "Use a radio:// URI for flight demos."
            )
        return explicit_uri

    log_preflight("Scanning for Crazyflies [...]")
    uris = scan_crazyflies()
    radio_uris = [candidate for candidate in uris if candidate.startswith("radio://")]

    if not radio_uris:
        raise PreflightError(
            "No Crazyflie found over radio. Check that the Crazyradio is connected, "
            "the Crazyflie is powered on, and the Windows USB driver is correct."
        )

    if len(radio_uris) > 1:
        formatted = "\n  - ".join(radio_uris)
        raise PreflightError(
            "Multiple Crazyflies were found. Set CF_URI before flying:\n"
            f"  - {formatted}"
        )

    selected = radio_uris[0]
    log_preflight(f"Crazyflie found: {selected}")
    return selected


def ensure_flow_deck(scf: SyncCrazyflie, timeout_s: float = 5.0) -> None:
    """Verify that the Flow Deck V2 is detected by the Crazyflie firmware."""
    detected = Event()
    callback_value: dict[str, int] = {}

    def _flow_callback(_name: str, value: str) -> None:
        parsed_value = int(value)
        callback_value["value"] = parsed_value
        if parsed_value:
            detected.set()

    scf.cf.param.add_update_callback(
        group="deck",
        name="bcFlow2",
        cb=_flow_callback,
    )

    request_update = getattr(scf.cf.param, "request_param_update", None)
    if callable(request_update):
        request_update("deck.bcFlow2")

    if not detected.wait(timeout=timeout_s):
        value = callback_value.get("value", 0)
        raise PreflightError(
            "Flow Deck V2 not detected "
            f"(deck.bcFlow2={value}). Flight aborted."
        )

    log_preflight("Flow Deck V2: OK")


def read_battery_voltage(
    scf: SyncCrazyflie,
    timeout_s: float = 2.0,
) -> float | None:
    """Read one ``pm.vbat`` sample from the Crazyflie.

    Returns ``None`` if battery telemetry is not available before the timeout.
    Missing telemetry does not fail pre-flight unless a minimum voltage has
    explicitly been configured.
    """
    received = Event()
    result: dict[str, float] = {}

    log_conf = LogConfig(name="PreflightBattery", period_in_ms=100)
    log_conf.add_variable("pm.vbat", "float")

    def _battery_callback(_timestamp, data, _logconf) -> None:
        if "pm.vbat" in data:
            result["voltage"] = float(data["pm.vbat"])
            received.set()

    try:
        scf.cf.log.add_config(log_conf)
        log_conf.data_received_cb.add_callback(_battery_callback)
        log_conf.start()

        if not received.wait(timeout=timeout_s):
            return None

        return result.get("voltage")
    except (KeyError, AttributeError):
        return None
    finally:
        try:
            log_conf.stop()
        except Exception:
            pass

        try:
            log_conf.delete()
        except Exception:
            pass


def print_physical_checklist() -> None:
    """Print the physical checks that software cannot verify automatically."""
    print()
    log_preflight("Manual physical checks:")
    log_preflight("  - correct propellers installed and firmly seated")
    log_preflight("  - battery and wires secured and clear of the propellers")
    log_preflight("  - Flow Deck facing the floor and unobstructed")
    log_preflight("  - USB cable disconnected from the Crazyflie")
    log_preflight("  - flight area clear around and above the drone")
    log_preflight("  - floor is matte, well lit, and textured enough for optical flow")
    print()


@contextmanager
def preflight_connection(
    uri: str | None = None,
    *,
    require_flow_deck: bool = True,
    battery_warning_v: float = DEFAULT_BATTERY_WARNING_V,
    min_battery_v: float | None = DEFAULT_MIN_BATTERY_V,
    show_physical_checklist: bool = True,
) -> Iterator[SyncCrazyflie]:
    """Open a Crazyflie connection after running the pre-flight checks.

    This function never starts the motors. Arming remains a separate explicit
    step so demos cannot start a flight merely by opening a connection.
    """
    if show_physical_checklist:
        print_physical_checklist()

    selected_uri = resolve_uri(uri)

    log_preflight(f"Connecting to {selected_uri} [...]")

    # No ro_cache/rw_cache path is supplied: no cache is persisted to disk.
    with SyncCrazyflie(selected_uri, cf=Crazyflie()) as scf:
        log_preflight("Radio connection: OK")

        protocol_version = scf.cf.platform.get_protocol_version()
        if protocol_version < 12:
            log_preflight(
                f"CRTP protocol: v{protocol_version} (legacy compatibility mode)"
            )
        else:
            log_preflight(f"CRTP protocol: v{protocol_version}")

        if require_flow_deck:
            ensure_flow_deck(scf)

        battery_v = read_battery_voltage(scf)

        if battery_v is None:
            log_preflight("Battery telemetry unavailable")
            if min_battery_v is not None:
                raise PreflightError(
                    "Battery voltage could not be verified while a minimum "
                    "voltage requirement is enabled."
                )
        else:
            log_preflight(f"Battery: {battery_v:.2f} V")

            if min_battery_v is not None and battery_v < min_battery_v:
                raise PreflightError(
                    f"Battery voltage too low: {battery_v:.2f} V "
                    f"< {min_battery_v:.2f} V."
                )

            if battery_v < battery_warning_v:
                log_preflight(
                    f"WARNING: battery voltage is below {battery_warning_v:.2f} V."
                )

        log_preflight("Automatic checks completed.")
        print()
        yield scf


@contextmanager
def armed(
    scf: SyncCrazyflie,
    *,
    settle_s: float = 1.0,
) -> Iterator[None]:
    """Arm the Crazyflie before flight and disarm it after landing.

    Current cflib versions transparently use the legacy arming command when
    connected to older firmware, which matches the behavior of the original
    working test-flight script.
    """
    log_flight("Arming [...]")
    scf.cf.supervisor.send_arming_request(True)
    time.sleep(settle_s)

    log_flight("Unlocking motor lock [...]")
    scf.cf.commander.send_setpoint(0.0, 0.0, 0.0, 0)
    time.sleep(0.1)

    try:
        yield
    finally:
        protocol_version = scf.cf.platform.get_protocol_version()

        if protocol_version >= 12:
            log_flight("Disarming [...]")
            scf.cf.supervisor.send_arming_request(False)
        else:
            log_flight("Legacy firmware: skipping explicit disarm.")


def log_diagnostic(message: str) -> None:
    """Print a consistently formatted diagnostic log message."""
    print(f"[diagnostic]\t{message}")


@contextmanager
def diagnostic_connection(
    uri: str | None = None,
    *,
    require_flow_deck: bool = False,
) -> Iterator[SyncCrazyflie]:
    """Open a checked radio connection for a non-flight diagnostic demo.

    Diagnostic demos reuse the radio, protocol and optional Flow Deck checks but
    do not require a flight-ready battery voltage and do not print the physical
    flight checklist.
    """
    with preflight_connection(
        uri,
        require_flow_deck=require_flow_deck,
        min_battery_v=None,
        show_physical_checklist=False,
    ) as scf:
        yield scf


def run_demo(main) -> None:
    """Run a demo entry point with consistent user-facing error handling."""
    try:
        main()
    except PreflightError as exc:
        print()
        log_preflight(f"FAILED: {exc}")
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        print()
        log_flight("Interrupted by user.")
        raise SystemExit(130)