"""The server that takes incoming WEI flow requests from the experiment application"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
import time
import cv2
import base64
import threading
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response#from a4s_camera_driver.a4s_camera_driver import A4S_camera_DRIVER  # import camera driverworkcell = None
global camera, state, image
serial_port = '/dev/ttyUSB1'
local_ip = 'parker.alcf.anl.gov'
local_port = '8000'
id1 = ""

def update_image():     
     global camera, image
     while (camera):
          image = camera.read()



@asynccontextmanager
async def lifespan(app: FastAPI):
     global camera, state
     """Initial run function for the app, parses the worcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized        Returns
        -------
        None"""
     parser = ArgumentParser()
     parser.add_argument("--host", type=str, help="host for client")
     parser.add_argument(
        "--port", type=int, help="port for client", default=None
     )
     parser.add_argument("--id", type=str, help="camera_id")
     args = parser.parse_args()
    
     id1 = args.id
     try:
            print(id1)
            if id1 == "0":
              id1 = 0
              print(id1)
            camera = cv2.VideoCapture(id1)
            threading.Thread(target=update_image).start()
 #           camera = A4S_camera_DRIVER(serial_port)
            state = "IDLE"
     except Exception as err:
            print(err)
            state = "ERROR"    # Yield control to the application
     yield    # Do any cleanup here
     pass

app = FastAPI(lifespan=lifespan, )
    
@app.get("/pic",  responses = {200: {
            "content": {"image/png": {}}
        }} , response_class=Response)
def get_state():
    global camera, state, image
    if state != "BUSY":
        #camera.get_status()
        #if camera.status_msg == 3:
                    #msg.data = 'State: ERROR'
                #    state = "ERROR"        #elif camera.status_msg == 0:
         #           state = "IDLE"
        pass
    print(image)
    im_png = cv2.imencode(".png", image[1])
    return Response(content=im_png[1].tobytes(), media_type="image/png")

@app.get("/state")
def get_state():
  return (JSONResponse(content={"State": "IDLE" }))
@app.get("/description")
async def description():
    global camera, state
    return JSONResponse(content={"State": state })#camera.get_status() })
@app.get("/resources")
async def resources():
    global camera, state
    return JSONResponse(content={"State": state })#camera.get_status() })
@app.post("/action", responses = {200: {
            "content": {"image/png": {}}
        }} , response_class=JSONResponse)
def do_action(
    action_handle: str,
    action_vars,
):    
    global image
    if action_handle == "take_picture":
     response={"action_response": "", "action_msg": "", "action_log": ""}
     im_png = cv2.imencode(".png", image[1])
     response["action_msg"] = base64.b64encode(im_png[1].tobytes()).decode()
     print(type(response["action_msg"]))
     return JSONResponse(content=response)
if __name__ == "__main__":
    import uvicorn
    parser = ArgumentParser()
    parser.add_argument("--host", type=str, help="host for client")
    parser.add_argument(
        "--port", type=int, help="port for client", default=None
    )
    parser.add_argument("--id", type=str, help="camera_id")
    args = parser.parse_args()
    
    uvicorn.run(
        "camera_rest_client:app",
        reload=False,
        host=args.host,
        port=args.port,
        ws_max_size=10000000000000000000000000000000000000000000000000000000000000000000000000,
    )
