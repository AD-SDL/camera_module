"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing_extensions import Annotated

import cv2
import numpy as np
from wei.types.step_types import (
    StepFileResponse,
    StepResponse,
    StepStatus,
    ActionRequest
)
from wei.utils import extract_version
from wei.modules.rest_module import RESTModule
from fastapi.datastructures import State

rest_module = RESTModule(
        name="camera_node",
        version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
        description="An example REST camera  implementation",
        model="camera"
        
)
rest_module.arg_parser.add_argument("--camera_address", type=str, help="the camera address", default="/dev/video0")


@rest_module.startup()
def startup(state: State):
     args = rest_module.arg_parser.parse_args
     state.camera_address = args.camera_address
     
@rest_module.action(name="take_picture", description="An action that atkes and returns a picture")
def take_picture(state: State, 
                 action: ActionRequest,
                 file_name: Annotated[str, "Name of the file to save"] = "image.jpg") -> StepResponse:
        """Function to take a picture"""
        image_name = file_name
        image_path = Path("~/.wei/temp").expanduser() / image_name
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

        return StepFileResponse(
            action_response=StepStatus.SUCCEEDED,
            path=image_path,
            action_log="",
        )

rest_module.start()
