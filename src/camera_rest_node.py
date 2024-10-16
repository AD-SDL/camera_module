"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""

from pathlib import Path

import cv2
import numpy as np
from fastapi.datastructures import State
from wei.modules.rest_module import RESTModule
from wei.types.module_types import LocalFileModuleActionResult
from wei.types.step_types import (
    ActionRequest,
    StepFileResponse,
    StepResponse,
    StepStatus,
)
from wei.utils import extract_version

rest_module = RESTModule(
    name="camera_node",
    version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
    description="An example REST camera implementation",
    model="camera",
)
rest_module.arg_parser.add_argument(
    "--camera_address",
    type=str,
    help="the address of the camera to attach",
    default="/dev/video1",
)


@rest_module.action(
    name="take_picture",
    description="An action that takes and returns a picture",
    results=[
        LocalFileModuleActionResult(
            label="image", description="the image taken from the camera"
        ),
    ],
)
def take_picture(
    state: State,
    action: ActionRequest,
) -> StepResponse:
    """Function to take a picture"""
    image_path = Path("~/.wei/temp").expanduser() / "image.jpg"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        camera = cv2.VideoCapture(state.camera_address)
        _, frame = camera.read()
        cv2.imwrite(str(image_path), frame)
        camera.release()
    except Exception:
        print("Camera unavailable, returning empty image")
        blank_image = np.zeros(shape=[512, 512, 3], dtype=np.uint8)
        cv2.imwrite(str(image_path), blank_image)

    return StepFileResponse(StepStatus.SUCCEEDED, files={"image": str(image_path)})


if __name__ == "__main__":
    rest_module.start()
