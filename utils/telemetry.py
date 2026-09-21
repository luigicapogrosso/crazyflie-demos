#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared telemetry helpers for Crazyflie demos."""

from __future__ import annotations

import time
from contextlib import contextmanager
from threading import Event
from typing import Callable, Iterator

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie


def log_telemetry(message: str) -> None:
    """Print a consistently formatted telemetry message."""
    print(f"[telemetry]\t{message}")


@contextmanager
def log_stream(
    scf: SyncCrazyflie,
    *,
    name: str,
    variables: list[str],
    period_ms: int = 100,
    callback: Callable | None = None,
) -> Iterator[LogConfig]:
    """Start a Crazyflie log block and always stop/delete it on exit."""
    log_conf = LogConfig(name=name, period_in_ms=period_ms)
    for variable in variables:
        log_conf.add_variable(variable)

    def _error_callback(_log_conf, message: str) -> None:
        log_telemetry(f"ERROR: {message}")

    scf.cf.log.add_config(log_conf)
    log_conf.error_cb.add_callback(_error_callback)
    if callback is not None:
        log_conf.data_received_cb.add_callback(callback)

    log_conf.start()
    try:
        yield log_conf
    finally:
        try:
            log_conf.stop()
        finally:
            try:
                log_conf.delete()
            except Exception:
                pass


def read_log_sample(
    scf: SyncCrazyflie,
    variables: list[str],
    *,
    timeout_s: float = 2.0,
    period_ms: int = 100,
) -> dict[str, float]:
    """Read one sample containing the requested log variables."""
    received = Event()
    sample: dict[str, float] = {}

    def _callback(_timestamp, data, _log_conf) -> None:
        sample.update(data)
        received.set()

    with log_stream(
        scf,
        name="OneSample",
        variables=variables,
        period_ms=period_ms,
        callback=_callback,
    ):
        if not received.wait(timeout=timeout_s):
            raise RuntimeError(
                f"Timed out while reading telemetry: {', '.join(variables)}"
            )

    return sample


def collect_log_samples(
    scf: SyncCrazyflie,
    variables: list[str],
    *,
    duration_s: float,
    period_ms: int = 100,
    name: str = "Collect",
) -> list[tuple[int, dict[str, float]]]:
    """Collect log samples for a fixed duration and return timestamp/data pairs."""
    samples: list[tuple[int, dict[str, float]]] = []

    def _callback(timestamp, data, _log_conf) -> None:
        samples.append((int(timestamp), dict(data)))

    with log_stream(
        scf,
        name=name,
        variables=variables,
        period_ms=period_ms,
        callback=_callback,
    ):
        time.sleep(duration_s)

    return samples