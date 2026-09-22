# Demo 07 - Battery sag during hover

## Description

Measure how much the battery voltage drops under motor load during a short hover.

**Type:** Flight + telemetry

## What You Need

Crazyflie 2.1+, Crazyradio 2.0, Flow Deck V2, charged battery, clear indoor flight area.

## Quick Start

From the repository root:

```bash
python -m 07_battery_sag_hover.main
```

## What Happens

- Starts battery logging.
- Hovers for 10 seconds.
- Lands.
- Prints maximum, minimum and observed voltage drop.