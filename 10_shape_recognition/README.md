# Demo 10 - Hand-Drawn Shape Recognition

## Description

Use the Crazyflie itself as a motion input device.
Move it by hand above the floor to draw a **line**, **square**, or **circle**.
The Flow Deck feeds motion into the estimator and the PC classifies the recorded XY trajectory using explainable geometric features.

After recognition, the program can optionally take off and fly a small canonical version of the detected shape.

### Sense, Interpret, Act

In this demo, the drone is moved by hand to draw a shape such as a line, square, or circle.
The Flow Deck records the motion, and the PC analyzes the trajectory to recognize which shape was drawn.

The system then reacts autonomously to the recognized shape, demonstrating a simple sense → interpret → act pipeline.
This gives the demo a stronger “intelligent system” feel because the drone is not only repeating motion, but interpreting it before deciding what to do.

## What You Need

- Crazyflie 2.1+
- Crazyradio 2.0
- Flow Deck V2
- a charged battery
- a matte, textured, well-lit floor
- clear indoor flight space if you choose the optional flight response

## Quick Start

From the repository root:

```bash
python -m 10_shape_recognition.main
```

## How To Draw

1. Hold the powered Crazyflie about 10-25 cm above the floor with the motors off.
2. Keep its front pointing in one fixed direction.
3. Press ENTER and draw one large, clear shape during the 8-second recording window.
4. For a line, make one long straight motion.
5. For a square or circle, return near the starting point.
6. The terminal prints the detected class and a heuristic confidence value.

## How Recognition Works

This demo does **not** use machine learning.
It computes geometric features from the Flow Deck based path, including:

- path straightness;
- start/end closure;
- bounding-box aspect ratio;
- radial consistency for circles;
- proximity to bounding-box edges for squares.

If the result is ambiguous, the classifier returns `UNKNOWN` and the drone does not fly.

## Optional Flight Response

When a shape is recognized, the demo asks before starting the motors.
The response flight is intentionally small:

- `LINE`: forward and back;
- `SQUARE`: 25 cm square;
- `CIRCLE`: 16 cm radius circle.