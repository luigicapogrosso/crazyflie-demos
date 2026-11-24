# Crazyflie Demos

Small Python demos for a **Bitcraze Crazyflie 2.1+**.
The repository is intentionally organized as a sequence of small, isolated demos.
Each demo lives in its own numbered folder and contains only the code specific to that experiment.
Shared connection and pre-flight logic lives in `utils/toolbox.py`.

---

## Installation Pipeline

### 1. Crazyradio Drivers & USB Permissions

Before communicating with the drone from your PC, configure USB access for the Crazyradio:

* **Windows:** Install the WinUSB driver using **Zadig** following the official [Bitcraze Windows USB Driver Guide](https://www.bitcraze.io/documentation/repository/crazyradio-firmware/master/building/usbwindows/).
* **Ubuntu/Linux:** Configure `udev` rules following the official [Bitcraze USB Permissions Guide](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/installation/usb_permissions/).

### 2. Python Environment

A dedicated Conda environment (Python 3.10 or 3.11) is recommended to keep dependencies isolated.

```bash
conda create -n crazyflie-demos python=3.12
conda activate crazyflie-demos
```

#### a) Install dependencies
Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

#### b) Verify the installation

```bash
python -m cfloader --help
```

**Windows Device Guard:** If `cfloader.exe` is blocked by Windows Device Guard policies, always invoke it through Python (`python -m cfloader ...`) instead of calling `cfloader` directly.

* **Official Documentation:**
  * [`cflib` Installation Guide](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/installation/install/)
  * [`cfclient` Installation Guide](https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/installation/install/)

---

### Firmware Build Toolchain

Firmware demos are built as **out-of-tree applications** using the Bitcraze App Layer.
On Windows, the official workflow uses **Ubuntu WSL** to compile the C firmware and **Windows Python (`cfloader`)** to flash it over Crazyradio.

* **Official Documentation:**
  * [Building and Flashing Crazyflie Firmware](https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/building-and-flashing/build/)
  * [Crazyflie App Layer User Guide](https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/userguides/app_layer/)

#### a) Install build tools (Ubuntu / Ubuntu WSL)

```bash
sudo apt update && sudo apt install -y git make build-essential gcc-arm-none-eabi python3
```

#### b) Clone `crazyflie-firmware` (with submodules)

Clone the repository into a Linux path **without spaces** (never inside `/mnt/c/` on WSL):

```bash
git clone --recursive [https://github.com/bitcraze/crazyflie-firmware.git](https://github.com/bitcraze/crazyflie-firmware.git)
```

When building an out-of-tree firmware demo, you will pass the path to this clone directly via `CRAZYFLIE_BASE=/path/to/crazyflie-firmware` in the `make` command.

---

### Restoring Stock Firmware

After testing a custom firmware demo, flash back the standard firmware so you can run the Python demos again:

1. Build the stock firmware on Linux / Ubuntu WSL:
   ```bash
   cd /path/to/crazyflie-firmware
   make cf2_defconfig
   make -j$(nproc)
   ```
2. Flash it over Crazyradio (with the Crazyflie turned on):
   ```powershell
   # From Windows Conda Prompt (WSL workflow)
   python -m cfloader -w radio://0/80/2M/E7E7E7E7E7 flash \\wsl.localhost\Ubuntu\home\<WSL_USER>\<PATH_TO>\crazyflie-firmware\build\cf2.bin stm32-fw
   ```
   *(On native Linux, simply run `CLOAD_CMDS="-w radio://0/80/2M/E7E7E7E7E7" make cload`.)*