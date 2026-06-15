from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
logger = logging.getLogger(__name__)
from app.api.routes.ask import router as ask_router
from app.api.routes.analyze import router as analyze_router
from app.retrieval.rule_loader import (
    get_loaded_authorities,
    load_rules,
)
from app.schemas import HealthResponse
from app.database import (
    init_db,
    AsyncSessionLocal,
)
from app.database_seed import (
    seed_guidelines_if_empty,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_rules()
    await init_db()

    async with AsyncSessionLocal() as db:
        await seed_guidelines_if_empty(db)

    logger.info(
        "Loaded authorities: %s",
        ", ".join(get_loaded_authorities())
    )

    logger.info("Medical Necessity Engine started.")
    yield
    logger.info("Medical Necessity Engine stopped.")

app = FastAPI(
    title="Medical Necessity Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask_router)
app.include_router(analyze_router)

@app.get("/")
async def root():
    return {
        "project": "Medical Necessity Engine",
        "version": "1.0.0",
        "status": "running",
    }

@app.get(
    "/health",
    response_model=HealthResponse,
)
async def health():
    return HealthResponse(status="ok")