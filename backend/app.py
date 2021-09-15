from asyncio import Queue

import cflib.crtp as crtp
import uvicorn
from fastapi import FastAPI

from backend.communication.crazyflie_drone_link import CrazyflieDroneLink
from backend.communication.message import Message

app = FastAPI()


@app.on_event("startup")
async def startup_event() -> None:
    crtp.init_drivers(enable_debug_driver=False)
    app.state.queue = Queue()
    app.state.crazyflie = await CrazyflieDroneLink.create("radio://0/80/250K/E7E7E7E7E7", app.state.queue)


@app.post("/test/send")
async def send(x: int, y: int, z: int) -> Message:
    queue: Queue = app.state.queue
    drone: CrazyflieDroneLink = app.state.crazyflie
    await drone.send_message(Message(x, y, z))
    response = await queue.get()
    return response


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="debug", reload=True, workers=1)
