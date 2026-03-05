import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.models import *  # noqa: F401,F403 — ensure all models registered for create_all
from app.routers.images import router as images_router
from app.routers.templates import router as templates_router, version_router
from app.routers.bundles import router as bundles_router
from app.routers.ocr import router as ocr_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    create_db_and_tables()
    yield


app = FastAPI(title="OCR System API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(images_router)
app.include_router(templates_router)
app.include_router(version_router)
app.include_router(bundles_router)
app.include_router(ocr_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
