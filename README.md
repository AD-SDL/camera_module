# camera_module

Provides a simple MADSci node for integrating web cameras to capture images.

See `definitions/camera_node_template.node.info.yaml` for details on the capabilities of this node, and `definitions/camera_node_template.node.yaml` as a template for your own Camera Node definition file.

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
python -m camera_rest_node --host 127.0.0.1 --port 2000
```

### Docker

- We provide a `Dockerfile` and example docker compose file (`compose.yaml`) to run this node dockerized.
- There is also a pre-built image available as `ghcr.io/ad-sdl/camera_module`.
- You can control the container user's id and group id by setting the `USER_ID` and `GROUP_ID`
