# Camera Driver

Contains the REST-based API for interfacing with the cameras in the RPL.

## Installation and Usage

```
git clone https://github.com/AD-SDL/camera_module.git
cd camera_module/scripts
python3 camera_rest_client.py --port=3001 --host=<hostname> --alias camera_module --camera_url=0
```

Change `camera_url` to point to the camera device you want to access.
