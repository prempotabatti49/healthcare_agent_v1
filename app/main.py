"""
Sunflower Health AI — FastAPI application entry point.
"""
# Load .env FIRST — before any other app import reads os.environ or secrets
from dotenv import load_dotenv
load_dotenv()

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config.settings import get_settings
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "A personalized AI health companion that remembers your health history, "
        "references your doctor's reports, and supports both physical and mental wellness."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    logging.getLogger(__name__).info("Starting %s …", settings.app_name)
    init_db()   # create tables if they don't exist


@app.on_event("shutdown")
def on_shutdown() -> None:
    logging.getLogger(__name__).info("Shutting down.")
