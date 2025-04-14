# camera_module

Provides a simple MADSci node for integrating web cameras to capture images.

See `camera_node_template.node.info.yaml` for details on the capabilities of this node, and `camera_node_template.node.yaml` as a template for your own Camera Node definition file.

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

You can use the `Dockerfile` and Docker Compose File (`compose.yaml`) as part of a docker (compose) setup. Note that you can set the container user's id and group id by setting the `USER_ID` and `GROUP_ID` variables in the container's environment.
