"""
REST-based node that interfaces with MADSci and provides a USB camera interface
"""

import tempfile
from pathlib import Path
from typing import Optional

import cv2
from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from pyzbar.pyzbar import decode

from camera_config import CameraConfig


class CameraNode(RestNode):
    """Node that interfaces with MADSci and provides a USB camera interface"""

    config_model = CameraConfig
    camera: cv2.VideoCapture = None

    @action
    def take_picture(
        self, focus: Optional[int] = None, autofocus: Optional[bool] = None
    ) -> ActionResult:
        """Action that takes a picture using the configured camera. The focus used can be set using the focus parameter."""
        camera = cv2.VideoCapture(self.config.camera_address)
        if not camera.isOpened():
            raise Exception("Unable to connect to camera")

        # * Handle autofocus/refocusing
        try:
            if focus is not None or autofocus is not None:
                self.logger.log_info("Adjusting focus settings")
                self.adjust_focus_settings(camera, focus, autofocus)
        except Exception as e:
            self.logger.log_error(f"Failed to adjust focus settings: {e}")

        success, frame = camera.read()
        if not success:
            if camera.isOpened():
                camera.release()
            raise Exception("Unable to read from camera")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = Path(temp_file.name)
            cv2.imwrite(str(temp_file_path), frame)
        camera.release()

        return ActionSucceeded(files={"image": temp_file_path})

    @action
    def read_barcode(
        self,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> ActionResult:
        """
        Takes an image and returns the values of any barcodes present in the image. Camera focus can be adjusted using the provided parameters if necessary.

        Args:
            camera (cv2.VideoCapture): The camera object to adjust focus for.
            focus (Optional[int]): The desired focus value (used if autofocus is disabled).
            autofocus (Optional[bool]): Whether to enable or disable autofocus.

        Returns:
            ActionSucceded regardless of if barcode is collected or not.
            Barcode field in ActionResult data dictionary will contain 'None' if no barcode was collected

        """
        try:
            # take an image and collect the image path
            action_result = self.take_picture(focus=focus, autofocus=autofocus)
            image_path = action_result.files["image"]

            # try to collect the barcode from the image
            image = cv2.imread(image_path)
            barcode = None

            all_detected_barcodes = decode(image)
            if all_detected_barcodes:
                # Note: only collects the first in a potential list of barcodes
                barcode = all_detected_barcodes[0].data.decode("utf-8")

        except Exception as e:
            raise e

        return ActionSucceeded(data={"barcode": barcode}, files={"image": image_path})

    def adjust_focus_settings(
        self,
        camera: cv2.VideoCapture,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> None:
        """
        Adjusts the camera's focus, if necessary/possible, based on the provided parameters.

        Args:
            camera (cv2.VideoCapture): The camera object to adjust focus for.
            focus (Optional[int]): The desired focus value (used if autofocus is disabled).
            autofocus (Optional[bool]): Whether to enable or disable autofocus.

        Raises:
            Exception: If the camera does not support autofocus or manual focus.
            ValueError: If the focus value is out of range.
        """
        focus_changed = False

        if autofocus is not None:
            self.logger.log_info(f"Setting autofocus to {autofocus}")
            current_autofocus = camera.get(cv2.CAP_PROP_AUTOFOCUS)
            if current_autofocus != (1 if autofocus else 0):
                camera.set(cv2.CAP_PROP_AUTOFOCUS, 1 if autofocus else 0)
                focus_changed = True

        if not autofocus and focus is not None:
            self.logger.log_info(f"Setting focus to {focus}")
            if focus < 0 or focus > 255:
                raise ValueError("Focus value must be between 0 and 255.")
            current_focus = camera.get(cv2.CAP_PROP_FOCUS)
            if current_focus != focus:
                camera.set(cv2.CAP_PROP_FOCUS, focus)
                focus_changed = True

        if focus_changed:
            self.logger.log_info(
                "Focus settings changed. Waiting for focus to stabilize."
            )
            for _ in range(30):  # Discard 30 frames to allow focus to stabilize
                camera.read()
        else:
            for _ in range(5): # Discard 5 frames in case the camera needs a moment for startup
                camera.read()


if __name__ == "__main__":
    camera_node = CameraNode()
    camera_node.start_node()
