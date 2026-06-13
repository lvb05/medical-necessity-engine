from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes.ask import router as ask_router
from app.api.routes.analyze import router as analyze_router
from app.retrieval.rule_loader import get_loaded_authorities, load_rules
from app.schemas import HealthResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_rules()
    print("Loaded authorities:", ", ".join(get_loaded_authorities()))
    print("Starting Medical Necessity Engine...")
    yield
    print("Stopping Medical Necessity Engine...")

app = FastAPI(
    title="Medical Necessity Engine",
    version="1.0.0",
    lifespan=lifespan,
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

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")