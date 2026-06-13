from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.retrieval.rule_loader import load_rules, get_loaded_authorities
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

@app.get("/")
async def root():
    return {
        "project": "Medical Necessity Engine",
        "version": "1.0.0",
        "status": "running",
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}