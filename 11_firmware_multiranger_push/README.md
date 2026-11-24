# 11 - Firmware Multi-Ranger Push Demo

On-board C application (Bitcraze App Layer) that enables autonomous, hand-guided flight on a **Crazyflie 2.1+** without requiring a host PC during flight.

## How It Works

The app runs an internal state machine directly on the STM32 microcontroller, reading distances from the **Multi-ranger deck** and holding position with the **Flow deck v2**:

1. **Idle / Unlock:** Place the Crazyflie on a flat surface and power it on. Wait for calibration to finish (red LED `M1` blinks rapidly). Wave your hand above the top sensor (`range.up`) to unlock and trigger takeoff.
2. **Hover & Push:** The drone climbs to the configured hover height (`height_sp`). Bring your hand close to the front, back, left, or right sensors to "push" the drone in the opposite direction.
3. **Land:** Place your hand above the top sensor again to initiate landing and shut down the motors.

## Hardware Required

* Crazyflie 2.1+
* Flow deck v2 (mounted on the bottom)
* Multi-ranger deck (mounted on the top)

---

## Building the Firmware (Ubuntu / Ubuntu WSL)

Make sure you have completed the [Firmware Build Toolchain](../README.md#3-firmware-build-toolchain-for-on-board-firmware-demos) setup.
Pass the path to your local `crazyflie-firmware` clone directly to `make`:

```bash
cd 11_firmware_multiranger_push
make CRAZYFLIE_BASE=/path/to/crazyflie-firmware cf2_defconfig
make CRAZYFLIE_BASE=/path/to/crazyflie-firmware -j$(nproc)
```

This generates the compiled binary at `build/cf2.bin`.

### Cleaning build artifacts

* `make CRAZYFLIE_BASE=/path/to/crazyflie-firmware clean` — removes compiled objects and `build/`, keeping `.config`.
* `make CRAZYFLIE_BASE=/path/to/crazyflie-firmware mrproper` — full clean including `.config` (requires running `cf2_defconfig` again).

---

## Flashing onto the Crazyflie 2.1+

Turn the Crazyflie **on** (normal mode) and plug in the Crazyradio.

### From Windows (Conda Prompt + WSL build)

```powershell
conda activate crazyflie-demos
python -m cfloader -w radio://0/80/2M/E7E7E7E7E7 flash \\wsl.localhost\Ubuntu\home\<WSL_USER>\<PATH_TO>\crazyflie-demos\11_firmware_multiranger_push\build\cf2.bin stm32-fw
```

### From Native Linux

```bash
CLOAD_CMDS="-w radio://0/80/2M/E7E7E7E7E7" make CRAZYFLIE_BASE=/path/to/crazyflie-firmware cload
```

*(Replace `radio://0/80/2M/E7E7E7E7E7` if your drone uses a custom radio channel or address.)*

---

## Customizing the Takeoff Height

To change the hover height, edit `height_sp` (in meters) inside `src/push.c`:

```c
static const float height_sp = 0.4f; // e.g., change to 0.8f for 80 cm
```

Recommended range: **0.3 m – 1.2 m** (Flow deck v2 provides best optical flow tracking within 1–2 m from the floor).
After editing, rebuild with `make CRAZYFLIE_BASE=/path/to/crazyflie-firmware -j$(nproc)` and flash `build/cf2.bin` again.