# camera_module

A simple module that supports capturing images with a USB camera or other video device.

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
python -m camera_rest_node --node_url http://localhost:2000
```

### Docker

You can use the Docker Compose File (`compose.yaml`) as part of a docker compose setup, or to inform a docker run command, to use this node via docker. Note that you can set the container user's id and group id using the `USER_ID` and `GROUP_ID` variable.
