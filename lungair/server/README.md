# LungAir's Backend Server

VolView's Python server can be used to run backend jobs such as deep learning inference pipelines.  
For details about the core VolView server, see the [quick-start guide](../../core/VolView/documentation/content/doc/server.md#starting-the-server).

## Instructions for running the LungAir server

### Step 1: [Install Poetry](https://python-poetry.org/docs/#installation)

### Step 2: Create and activate a Python 3.9 virtual environment in the current directory

```bash
python3.9 -m venv .venv
source .venv/bin/activate
```

### Step 3: Set up the core server and dependencies

```bash
export SOURCE_DIR=/path/to/source/lungair-web-application

cd $SOURCE_DIR/core/VolView/server

poetry install

export PYTHONPATH=$PYTHONPATH:$SOURCE_DIR/core/VolView/server
```

### Step 4: Install dependencies for _LungAir Methods_

```bash
cd $SOURCE_DIR/lungair/server

poetry install --no-root
```

> NOTE: While the above command installs all Python requirements for the server,
> _PyTorch_ also requires its corresponding CUDA Toolkit version (e.g., 12.1) to
> be installed on the system.

### Step 5: Download the lungs segmentation model

```bash
curl https://data.kitware.com/api/v1/file/65bd8c2f03c3115909f73dd7/download --output segmentLungsModel-v1.0.ckpt
```

### Step 6: Start the server

```bash
poetry run python -m volview_server -P 4014 -H 0.0.0.0 lungair_methods.py
```

> NOTE: You may need to remove the `-P` (port) argument if it is not parsed
> properly by a downstream file.
