# Demo 00 - Test flight

## Description

Take off to 30 cm, hover for 3 seconds and land. This is the baseline check before running any trajectory demo.

**Type:** Flight

## What You Need

Crazyflie 2.1+, Crazyradio 2.0, Flow Deck V2, charged battery, clear indoor flight area.

## Quick Start

From the repository root:

```bash
python -m 00_test_flight.main
```

## What Happens

- Runs the shared pre-flight checks.
- Arms the Crazyflie.
- Takes off to about 0.30 m.
- Hovers for 3 seconds.
- Lands and disarms.