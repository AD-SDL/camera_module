from madsci.common.types.node_types import RestNodeConfig
from typing import Union

class CameraConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    camera_address: Union[int, str] = 0
    """The camera address."""
    file_path: str = "~/.wei/temp"
