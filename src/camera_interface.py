"""
Camera interface for handling camera operations including image capture and barcode reading.
"""

import tempfile
import threading
from pathlib import Path
from typing import Optional, Union

import cv2

try:
    from pyzbar.pyzbar import decode
except ImportError:
    decode = None
    print("pyzbar not found, barcode reading functionality will be disabled.")  # noqa: T201


class CameraInterface:
    """Interface for camera operations."""

    def __init__(self, camera_address: Union[int, str] = 0) -> None:
        """
        Initialize the camera interface.

        Args:
            camera_address: The camera address, either a number for windows or a device path in Linux/Mac.
        """
        self.camera_address = self._validate_camera_address(camera_address)
        self.camera: Optional[cv2.VideoCapture] = None
        self.camera_lock = threading.Lock()

    @staticmethod
    def _validate_camera_address(camera_address: Union[int, str]) -> Union[int, str]:
        """
        Validates that, if the camera address is a string that can be converted to an integer, it does so.

        Args:
            camera_address: The camera address to validate.

        Returns:
            The validated camera address as int or str.
        """
        try:
            return int(camera_address)
        except (ValueError, TypeError):
            return camera_address

    def connect(self) -> None:
        """
        Connect to the camera.

        Raises:
            Exception: If unable to connect to camera.
        """
        with self.camera_lock:
            self.camera = cv2.VideoCapture(self.camera_address)
            if not self.camera.isOpened():
                raise Exception("Unable to connect to camera")

    def disconnect(self) -> None:
        """Disconnect from the camera if connected."""
        with self.camera_lock:
            if self.camera is not None and self.camera.isOpened():
                self.camera.release()
                self.camera = None

    def is_connected(self) -> bool:
        """
        Check if the camera is connected.

        Returns:
            True if camera is connected, False otherwise.
        """
        with self.camera_lock:
            return self.camera is not None and self.camera.isOpened()

    def take_picture(
        self, focus: Optional[int] = None, autofocus: Optional[bool] = None
    ) -> Path:
        """
        Take a picture using the configured camera.

        Args:
            focus: The desired focus value (used if autofocus is disabled).
            autofocus: Whether to enable or disable autofocus.

        Returns:
            Path to the captured image file.

        Raises:
            Exception: If unable to read from camera or camera is not connected.
        """
        with self.camera_lock:
            if self.camera is None or not self.camera.isOpened():
                raise Exception("Camera is not connected")

            # Handle autofocus/refocusing
            if focus is not None or autofocus is not None:
                self._adjust_focus_settings_unlocked(focus, autofocus)

            success, frame = self.camera.read()
            if not success:
                raise Exception("Unable to read from camera")

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_file_path = Path(temp_file.name)
                cv2.imwrite(str(temp_file_path), frame)

            return temp_file_path

    def read_barcode(
        self,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> tuple[str, Path]:
        """
        Take an image and return the values of any barcodes present in the image.

        Args:
            focus: The desired focus value (used if autofocus is disabled).
            autofocus: Whether to enable or disable autofocus.

        Returns:
            A tuple containing:
                - The barcode string (empty if no barcode found)
                - Path to the captured image

        Raises:
            ImportError: If pyzbar is not installed.
            Exception: If unable to capture image or read from camera.
        """
        # Take an image and collect the image path
        image_path = self.take_picture(focus=focus, autofocus=autofocus)

        # Try to collect the barcode from the image
        image = cv2.imread(str(image_path))
        barcode = ""

        if decode is None:
            raise ImportError("pyzbar is not installed, cannot read barcodes.")

        all_detected_barcodes = decode(image)
        if all_detected_barcodes:
            # Note: only collects the first in a potential list of barcodes
            barcode = all_detected_barcodes[0].data.decode("utf-8")

        return barcode, image_path

    def adjust_focus_settings(
        self,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> None:
        """
        Adjust the camera's focus, if necessary/possible, based on the provided parameters.

        Args:
            focus: The desired focus value (used if autofocus is disabled).
            autofocus: Whether to enable or disable autofocus.

        Raises:
            Exception: If camera is not connected.
            ValueError: If the focus value is out of range.
        """
        with self.camera_lock:
            self._adjust_focus_settings_unlocked(focus, autofocus)

    def _adjust_focus_settings_unlocked(
        self,
        focus: Optional[int] = None,
        autofocus: Optional[bool] = None,
    ) -> None:
        """
        Internal method to adjust camera focus without acquiring the lock.
        This should only be called when the camera_lock is already held.

        Args:
            focus: The desired focus value (used if autofocus is disabled).
            autofocus: Whether to enable or disable autofocus.

        Raises:
            Exception: If camera is not connected.
            ValueError: If the focus value is out of range.
        """
        if self.camera is None or not self.camera.isOpened():
            raise Exception("Camera is not connected")

        focus_changed = False

        if autofocus is not None:
            current_autofocus = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
            if current_autofocus != (1 if autofocus else 0):
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1 if autofocus else 0)
                focus_changed = True

        if not autofocus and focus is not None:
            if focus < 0 or focus > 255:
                raise ValueError("Focus value must be between 0 and 255.")
            current_focus = self.camera.get(cv2.CAP_PROP_FOCUS)
            if current_focus != focus:
                self.camera.set(cv2.CAP_PROP_FOCUS, focus)
                focus_changed = True

        if focus_changed:
            # Discard 30 frames to allow focus to stabilize
            for _ in range(30):
                self.camera.read()
        else:
            # Discard 5 frames in case the camera needs a moment for startup
            for _ in range(5):
                self.camera.read()
