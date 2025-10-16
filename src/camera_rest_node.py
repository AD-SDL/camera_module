"""
REST-based node that interfaces with MADSci and provides a USB camera interface
"""

import tempfile
from pathlib import Path
from typing import Annotated, Optional, Union

import cv2
from madsci.common.types.node_types import RestNodeConfig
from madsci.common.types.resource_types import Slot
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from pyzbar.pyzbar import decode


class CameraNodeConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    camera_address: Union[int, str] = 0
    """The camera address, either a number for windows or a device path in Linux/Mac."""


class CameraNode(RestNode):
    """Node that interfaces with MADSci and provides a USB camera interface"""

    config: CameraNodeConfig = CameraNodeConfig()
    config_model = CameraNodeConfig
    camera: cv2.VideoCapture = None

    def startup_handler(self) -> None:
        """Called to (re)initialize the node. Should be used to open connections to devices or initialize any other resources."""

        # Create picture capture deck template
        capture_deck_slot = Slot(
            resource_name="camera_capture_deck",
            resource_class="CameraCaptureDeck",
            capacity=1,
            attributes={
                "slot_type": "capture_deck",
                "can_capture": True,
                "light": "on",
                "description": "Camera capture deck where items are placed for imaging",
            },
        )

        self.resource_client.init_template(
            resource=capture_deck_slot,
            template_name="camera_capture_deck_slot",
            description="Template for camera capture deck slot. Represents the position where items are placed for picture taking.",
            required_overrides=["resource_name"],
            tags=["camera", "capture", "deck", "slot", "imaging"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # Initialize capture deck resource
        deck_resource_name = "camera_capture_deck_" + str(
            self.node_definition.node_name
        )
        self.capture_deck = self.resource_client.create_resource_from_template(
            template_name="camera_capture_deck_slot",
            resource_name=deck_resource_name,
            add_to_database=True,
        )
        self.logger.log(
            f"Initialized capture deck resource from template: {self.capture_deck.resource_id}"
        )

        self.camera = cv2.VideoCapture(self.config.camera_address)
        if not self.camera.isOpened():
            raise Exception("Unable to connect to camera")
        self.logger.log("Camera node initialized!")

    def state_handler(self) -> None:
        """Periodically called to update the current state of the node."""
        if self.camera is not None:
            self.node_state = {"camera_status": "connected"}
            self.logger.log("Camera is operational.")
        else:
            self.node_state = {"camera_status": "disconnected"}
            self.logger.log_warning("Camera is not connected.")

    @action
    def take_picture(
        self, focus: Optional[int] = None, autofocus: Optional[bool] = None
    ) -> Annotated[Path, "The picture taken by the camera"]:
        """Action that takes a picture using the configured camera. The focus used can be set using the focus parameter."""

        # * Handle autofocus/refocusing
        try:
            if focus is not None or autofocus is not None:
                self.logger.log_info("Adjusting focus settings")
                self.adjust_focus_settings(self.camera, focus, autofocus)
        except Exception as e:
            self.logger.log_error(f"Failed to adjust focus settings: {e}")

        success, frame = self.camera.read()
        if not success:
            if self.camera.isOpened():
                self.camera.release()
            raise Exception("Unable to read from camera")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = Path(temp_file.name)
            cv2.imwrite(str(temp_file_path), frame)
        self.camera.release()

        return temp_file_path

    @action
    def read_barcode(
        self,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> tuple[
        Annotated[
            str, "The barcode read from the image, or None if no barcode was found"
        ],
        Annotated[Path, "The picture taken by the camera"],
    ]:
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
            image_path = self.take_picture(focus=focus, autofocus=autofocus)

            # try to collect the barcode from the image
            image = cv2.imread(image_path)
            barcode = None

            all_detected_barcodes = decode(image)
            if all_detected_barcodes:
                # Note: only collects the first in a potential list of barcodes
                barcode = all_detected_barcodes[0].data.decode("utf-8")

        except Exception as e:
            raise e

        return barcode, image_path

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
            for _ in range(
                5
            ):  # Discard 5 frames in case the camera needs a moment for startup
                camera.read()


if __name__ == "__main__":
    camera_node = CameraNode()
    camera_node.start_node()
