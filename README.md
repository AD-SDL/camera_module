# camera_module

A MADSci node module that exposes a USB/video camera as a REST service. Supports image capture and barcode reading via [OpenCV](https://opencv.org/) and [pyzbar](https://pypi.org/project/pyzbar/).

## Configuration

All configuration is done via environment variables (prefixed `NODE_`) or a `settings.yaml` file. See [docs/Configuration.md](docs/Configuration.md) for the full reference and [`.env.example`](.env.example) for a commented template.

The most common settings to override:

| Variable | Default | Purpose |
|---|---|---|
| `NODE_CAMERA_ADDRESS` | `0` | Camera index (int) or device path (e.g. `/dev/video0`) |
| `NODE_URL` | `http://127.0.0.1:2000/` | URL the node binds to and advertises |
| `NODE_NODE_NAME` | _(class name)_ | Human-readable name registered with MADSci |

## Getting Started

### Option 1 — Devbox (recommended)

[Devbox](https://www.jetify.com/devbox) provides a reproducible shell with Python 3.12, pdm, uv, ruff, and just pre-installed.

```bash
devbox shell        # enter the reproducible environment
just init           # install dependencies + pre-commit hooks
```

### Option 2 — PDM

```bash
pdm install -G:all  # install all dependencies including dev extras
```

### Option 3 — pip / uv (minimal)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install .
```

> **Linux/Mac:** `pyzbar` requires the native `zbar` library. Install it with:
> - Debian/Ubuntu: `sudo apt install libzbar0`
> - macOS: `brew install zbar`
>
> Without it, `take_picture` still works; `read_barcode` will raise `ImportError`.

## Running the Node

```bash
python -m camera_rest_node
```

The host, port, and all other settings can be set via environment variables or `settings.yaml` (discovered by walking up the directory tree). See [docs/Configuration.md](docs/Configuration.md).

## Development

```bash
just checks   # ruff lint + format (via pre-commit, auto-fixes then re-checks)
just test     # pytest
just dcb      # docker compose build
```

## Docker

A pre-built image is available at `ghcr.io/ad-sdl/camera_module`. To run with Docker Compose:

```bash
# Copy and edit the example env file
cp .env.example .env

docker compose up
```

The container runs with `privileged: true` and `network_mode: host` so it can access `/dev/video*`. The `madsci` user inside the container is added to the `video` group automatically.

Set `USER_ID` and `GROUP_ID` to match your host user to avoid file permission issues with volume-mounted paths:

```bash
USER_ID=$(id -u) GROUP_ID=$(id -g) docker compose up
```

The `settings.yaml` and `.madsci/` directory are bind-mounted from the project root into the container.
