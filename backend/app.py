import os
from typing import Final

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.drone_registry import initiate_links
from backend.routers.argos import router as argos_router
from backend.routers.common import router as common_router
from backend.routers.crazyflie import router as crazyflie_router

ONLY_SERVE_OPENAPI_SCHEMA_ENV_VAR: Final = "ONLY_SERVE_OPENAPI_SCHEMA"

TAGS_METADATA: Final = [
    {
        "name": "argos",
        "description": "Endpoints that target only the Argos (simulated) drones",
    },
    {
        "name": "common",
        "description": "Endpoints that target all the drones",
    },
    {
        "name": "crazyflie",
        "description": "Endpoints that target only the Crazyflie drones",
    },
]

app = FastAPI(
    title="Backend",
    description="Serving request from the WebUI to the Crazyflie and Argos drones 🚀",
    openapi_tags=TAGS_METADATA,
    servers=[
        {"url": "http://backend:8080/api", "description": "Release endpoint"},
        {"url": "http://localhost:8000", "description": "Development endpoint"},
    ],
    version=__version__,
)

app.include_router(argos_router)
app.include_router(common_router)
app.include_router(crazyflie_router)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
async def startup_event() -> None:
    if not os.getenv(ONLY_SERVE_OPENAPI_SCHEMA_ENV_VAR):
        await initiate_links()


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="debug", reload=True, workers=1)
