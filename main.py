from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router


# ---------------------------------------------------------
# BASE DIRECTORY
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"

# Create folders automatically
STATIC_DIR.mkdir(exist_ok=True)
PANELS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description=(
        "AI-powered comic story generator using "
        "Gemini and Stable Diffusion."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

app.include_router(router)


# ---------------------------------------------------------
# ROOT HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "running",
        "application": "ComicCraft",
    }