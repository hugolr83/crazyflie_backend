import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.drone_registry import initiate_links
from backend.routers.argos import router as argos_router
from backend.routers.common import router as common_router
from backend.routers.crazyflie import router as crazyflie_router

app = FastAPI()

app.include_router(argos_router)
app.include_router(common_router)
app.include_router(crazyflie_router)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
async def startup_event() -> None:
    await initiate_links()


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="debug", reload=True, workers=1)
