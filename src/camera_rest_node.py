"""
REST-based node that interfaces with MADSci and provides a USB camera interface
"""

import traceback
from pathlib import Path
from typing import Annotated, Any, Optional, Union

from madsci.common.ownership import get_current_ownership_info
from madsci.common.types.node_types import RestNodeConfig
from madsci.common.types.resource_types import Slot
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from pydantic import field_validator

from camera_interface import CameraInterface


class CameraNodeConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    camera_address: Union[int, str] = 0
    """The camera address, either a number for windows or a device path in Linux/Mac."""

    @field_validator("camera_address", mode="after")
    @classmethod
    def ensure_int_camera_address(cls, v: Any) -> Union[int, str]:
        """Validates that, if the camera address is a string that can be converted to an integer, it does so."""
        try:
            return int(v)
        except (ValueError, TypeError):
            return v


class CameraNode(RestNode):
    """Node that interfaces with MADSci and provides a USB camera interface"""

    config: CameraNodeConfig = CameraNodeConfig()
    config_model = CameraNodeConfig
    camera_interface: Optional[CameraInterface] = None
    state_error_latch: bool = False

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
            overrides={"owner": get_current_ownership_info().model_dump(mode="json")},
        )
        self.logger.log(
            f"Initialized capture deck resource from template: {self.capture_deck.resource_id}"
        )

        # Initialize camera interface
        self.camera_interface = CameraInterface(self.config.camera_address)
        # Test camera connection
        if self.camera_interface.test_connection():
            self.logger.log("Camera node initialized!")
        else:
            self.logger.log_error("Failed to connect to camera during initialization")
            raise Exception("Unable to connect to camera")

    def state_handler(self) -> None:
        """Periodically called to update the current state of the node."""
        camera_status = "disconnected"
        try:
            if self.camera_interface is not None:
                # Test if camera can be connected
                if self.camera_interface.test_connection():
                    camera_status = "connected"
                else:
                    camera_status = "disconnected"
                    if not self.state_error_latch:
                        self.logger.log_error("Camera connection test failed")
                        self.node_status.errors.append("Camera connection test failed")
                        self.node_status.errored = True
                    self.state_error_latch = True
        except Exception:
            camera_status = "disconnected"
            if not self.state_error_latch:
                self.logger.log_error(traceback.format_exc())
                self.node_status.errors.append(traceback.format_exc())
                self.node_status.errored = True
            self.state_error_latch = True
        finally:
            if camera_status == "connected":
                self.state_error_latch = False
                self.node_status.errored = False
            self.node_state = {"camera_status": camera_status}

    @action
    def take_picture(
        self, focus: Optional[int] = None, autofocus: Optional[bool] = None
    ) -> Annotated[Path, "The picture taken by the camera"]:
        """Action that takes a picture using the configured camera. The focus used can be set using the focus parameter."""

        if self.camera_interface is None:
            raise Exception("Camera interface is not initialized")

        try:
            image_path = self.camera_interface.take_picture(
                focus=focus, autofocus=autofocus
            )
            self.logger.log_info(f"Picture taken and saved to {image_path}")
            return image_path
        except Exception as e:
            self.logger.log_error(f"Failed to take picture: {e}")
            raise

    @action
    def read_barcode(
        self,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> tuple[
        Annotated[
            str,
            "The barcode read from the image, or an empty string if no barcode was found",
        ],
        Annotated[Path, "The picture taken by the camera"],
    ]:
        """
        Takes an image and returns the values of any barcodes present in the image. Camera focus can be adjusted using the provided parameters if necessary.

        Args:
            focus (Optional[int]): The desired focus value (used if autofocus is disabled).
            autofocus (Optional[bool]): Whether to enable or disable autofocus.

        Returns:
            A tuple containing:
                - The barcode string (empty if no barcode found)
                - Path to the captured image

        """
        if self.camera_interface is None:
            raise Exception("Camera interface is not initialized")

        try:
            barcode, image_path = self.camera_interface.read_barcode(
                focus=focus, autofocus=autofocus
            )
            if barcode:
                self.logger.log_info(f"Barcode read: {barcode}")
            else:
                self.logger.log_info("No barcode detected in image")
            return barcode, image_path
        except Exception as e:
            self.logger.log_error(f"Failed to read barcode: {e}")
            raise


if __name__ == "__main__":
    camera_node = CameraNode()
    camera_node.start_node()
