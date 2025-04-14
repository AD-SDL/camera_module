"""Configuration class for the camera node module."""

from typing import Union

from madsci.common.types.node_types import RestNodeConfig


class CameraConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    camera_address: Union[int, str] = 0
    """The camera address, either a number for windows or a device path in Linux/Mac."""
