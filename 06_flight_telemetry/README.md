# Demo 06 - Flight telemetry

## Description

Hover while streaming estimated position, yaw and battery voltage to the terminal.

**Type:** Flight + telemetry

## What You Need

Crazyflie 2.1+, Crazyradio 2.0, Flow Deck V2, charged battery, clear indoor flight area.

## Quick Start

From the repository root:

```bash
python -m 06_flight_telemetry.main
```

## What Happens

- Starts a telemetry log block.
- Takes off and hovers for 10 seconds.
- Prints live stateEstimate, yaw and battery values.
- Lands.