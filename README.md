# Crazyflie Demos

Small Python demos for a **Bitcraze Crazyflie 2.1+**.
The repository is intentionally organized as a sequence of small, isolated demos.
Each demo lives in its own numbered folder and contains only the code specific to that experiment.
Shared connection and pre-flight logic lives in `utils/toolbox.py`.

## Installation

### 1. Create a Python environment

It is recommended to use a Conda environment to manage the project's dependencies.

```bash
conda create -n crazyflie-demos python=3.12
conda activate crazyflie-demos
```

**3. Install Dependencies**
Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```