# camera_module

A simple module that supports taking snapshots with a camera or other video device.

## Installation and Usage

### Python

```bash
# Create a virtual environment named .venv
python -m venv .venv

# Activate the virtual environment on Linux or macOS
source .venv/bin/activate

# Alternatively, activate the virtual environment on Windows
# .venv\Scripts\activate

# Install the module and dependencies in the venv
pip install .

# Run the environment
python src/camera_rest_node.py --host 0.0.0.0 --port 2000
```

### Docker

1. Install Docker for your platform of choice.
2. Run `make init` to create the `.env` file, or copy `example.env` to `.env`
3. Open the `.env` file and ensure that all values are set and correct.
    1. Check that the `USER_ID` and `GROUP_ID` are correct, as these ensure correct file permissions (in most cases, they should match your user's UID and GID)
    2. Check that the `WEI_DATA_DIR` and `REDIS_DIR` directories exist and have the appropriate permissions
    3. The `DEVICE` variable can be used to determine which camera device is used by the module

```bash
# Build and run just the module
docker compose up --build

# Run the module, but detach so you can keep working in the same terminal
docker compose up --build -d

# Run the module alongside a simple workcell (for testing)
docker compose --profile wei up --build -d
```
