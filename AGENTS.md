# AGENTS.md/CLAUDE.md

This file provides guidance to AI coding agents. Note that AGENTS.md and CLAUDE.md are symlinked.

## Overview

`camera_module` is a standalone MADSci node module that exposes a USB/video camera as a REST service. It uses `opencv-python-headless` for capture and `pyzbar` for barcode decoding. The node registers with MADSci, manages a resource template ("capture deck slot"), and exposes two actions: `take_picture` and `read_barcode`.

## Source Layout

```
src/
  camera_rest_node.py   # CameraNode (RestNode subclass) — MADSci integration, actions, state/startup handlers
  camera_interface.py   # CameraInterface — pure OpenCV/pyzbar logic, no MADSci dependency
```

All source files are directly in `src/` (flat layout, not a package). The entry point is `python -m camera_rest_node`.

## Key Architecture Points

- **`CameraNode`** inherits from `madsci.node_module.rest_node_module.RestNode`. It owns `startup_handler` (called on init/re-init) and `state_handler` (polled periodically to update node status).
- **`CameraInterface`** holds a `threading.Lock` to serialize camera access. The camera is opened/closed per operation (not kept open). `pyzbar` import is wrapped in a try/except — if the native `libzbar0` library is missing, barcode reading raises `ImportError` at call time rather than at import.
- **Resource template**: On startup, the node registers a `Slot` resource template (`camera_capture_deck_slot`) via `resource_client`, then instantiates it per node name. This is required for MADSci resource tracking.
- **Focus control**: `_adjust_focus_settings_unlocked` must only be called while `camera_lock` is held. After a focus change it discards 30 frames to stabilize; otherwise 5 frames for startup.
- **`camera_address`**: Accepts `int` (device index, Windows) or `str` (device path, Linux/Mac, e.g. `/dev/video0`). A field validator on `CameraNodeConfig` coerces numeric strings to int.

## Development Commands

Uses `just` + `pdm` (with `uv` as backend). Devbox provides a reproducible shell (Python 3.12, pdm, uv, ruff, just).

```bash
just init      # pdm install -G:all + pre-commit install
just checks    # ruff lint + format via pre-commit (runs twice to verify fixes applied)
just dcb       # docker compose build
just test      # pytest (no automated tests currently — only a notebook in tests/)
```

Direct run (after `pip install .` or `just init`):
```bash
python -m camera_rest_node --host 127.0.0.1 --port 2000
```

Node configuration is driven by `settings.yaml` (MADSci settings discovery walks up from the working directory).

## Linting

Ruff with a broad rule set (see `ruff.toml`). Notable ignores: `E501` (line length), `ANN401` (Any types), `COM812`. Tests may use `S101` (assert). Line length is 88, double quotes, spaces.

## Docker

```bash
docker compose up          # runs using ghcr.io/ad-sdl/camera_module
docker compose build       # or: just dcb
```

The container runs `privileged: true` with `network_mode: host` so it can access `/dev/video*`. User in the container is added to the `video` group. `USER_ID`/`GROUP_ID` build args control file ownership. The `settings.yaml` and `.madsci/` directory are volume-mounted.

Base image: `ghcr.io/ad-sdl/madsci`. Package is installed with `uv pip install -e` inside the MADSci venv (`$MADSCI_VENV`).

## Platform Notes

- On Linux/Mac, install `libzbar0` (apt) or `zbar` (brew) for barcode support; the Docker image installs this automatically.
- Camera address on Linux is typically `/dev/video0` (string); on Windows use an integer index.
