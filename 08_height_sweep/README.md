# Demo 08 - Height sweep

## Description

Step through several heights while printing both the Flow Deck range measurement and the estimator height.

**Type:** Flight + Flow telemetry

## What You Need

Crazyflie 2.1+, Crazyradio 2.0, Flow Deck V2, charged battery, clear indoor flight area.

## Quick Start

From the repository root:

```bash
python -m 08_height_sweep.main
```

## What Happens

- Takes off to 0.30 m.
- Climbs in 0.80 m steps.
- Descends in 0.80 m steps.
- Streams range.zrange and stateEstimate.z.
- Lands.