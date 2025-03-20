"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""

from pathlib import Path
from camera_config import CameraConfig
import tempfile
import cv2
from madsci.common.types.action_types import FileActionResultDefinition
from madsci.common.types.action_types import ActionResult, ActionSucceeded, ActionFailed
from madsci.common.types.node_types import RestNodeConfig
from madsci.node_module.abstract_node_module import action
from madsci.node_module.rest_node_module import RestNode
from madsci.client.event_client import EventClient
import time
from typing import Union



class CameraNode(RestNode):

    config_model = CameraConfig
    logger = EventClient()

    @action(name="take_picture", description="take a picture, can set the focus")
    def take_picture(self, focus: float=100
)   -> ActionResult:
        """Function to take a picture"""
        image_path = Path(self.config.file_path).expanduser() / "image.jpg"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            camera = cv2.VideoCapture(self.config.camera_address)
            camera.set(cv2.CAP_PROP_FOCUS, focus)
            for i in range(10):
                _, frame = camera.read()
                time.sleep(0.1)
            cv2.imwrite(str(image_path), frame)
            camera.release()
        except Exception:
            return ActionFailed(
            errors="Unable to connect to camera"
        )

        return ActionSucceeded(files={"image": image_path})


if __name__ == "__main__":
    camera_node = CameraNode()
    camera_node.start_node()
