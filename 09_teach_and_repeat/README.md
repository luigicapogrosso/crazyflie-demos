# Demo 09 - Teach and Repeat

## Description

Teach the Crazyflie a short path by moving it by hand while the motors are off.
The Flow Deck feeds local XY motion into the estimator, the PC records the trajectory, filters it, simplifies it, applies conservative size limits, and then asks for confirmation before replaying it in flight.

### Learning by Demonstration

Instead of programming a trajectory manually, you physically teach the drone a path by moving it with your hand.
The system records the motion with the Flow Deck, converts it into a trajectory, and then replays it autonomously.

This is a simple example of Learning from Demonstration (LfD): the robot learns a behavior from a human demonstration rather than from explicit trajectory programming.
It is not machine learning, but it follows the same idea of teaching by example.

## What You Need

- Crazyflie 2.1+
- Crazyradio 2.0
- Flow Deck V2
- a charged battery
- a matte, textured, well-lit floor
- roughly 1.5 x 1.5 m of clear flight space

## Quick Start

From the repository root:

```bash
python -m 09_teach_and_repeat.main
```

## How To Teach The Path

1. Keep the motors off and hold the powered Crazyflie about 10-25 cm over the floor.
2. Keep the **front of the drone pointing in the same direction** for the whole teaching motion.
3. Press ENTER and move the drone slowly for 8 seconds.
4. The program filters and simplifies the recorded path.
5. Return the drone to the original launch point with the same heading.
6. Confirm the replay only when the area is clear.

## Safety Limits

The learned path is automatically scaled if it is too large or too long.
The replay is intentionally slow and uses a limited number of segments.

## Important Limitation

The Flow Deck provides local motion estimation.
It is not a global positioning system.
`MotionCommander` uses relative velocity-based motion, so replay is approximate and error can accumulate.
Keep paths short and avoid rotating the drone while teaching.