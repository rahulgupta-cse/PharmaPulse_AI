"""
Main application entry point for the AI-CRM HCP Module backend.

Configures the FastAPI application with CORS middleware, registers
all API routers, creates database tables on startup, seeds sample
data if the database is empty, and provides a health-check endpoint.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base, get_db_session
from models import HCP, Interaction, Product  # noqa: F401 — ensures tables are registered
from seed_data import seed_database

from routes.interactions import router as interactions_router
from routes.hcp import router as hcp_router
from routes.agent import router as agent_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown logic
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup:
      1. Creates all database tables that don't yet exist.
      2. Seeds the database with sample data if tables are empty.

    On shutdown:
      Performs any necessary cleanup (currently a no-op placeholder).
    """
    # --- Startup ---
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # Seed data if the database is empty
    db = get_db_session()
    try:
        hcp_count = db.query(HCP).count()
        if hcp_count == 0:
            logger.info("Database is empty — seeding sample data...")
            counts = seed_database(db)
            logger.info(f"Seed complete: {counts}")
        else:
            logger.info(f"Database already contains {hcp_count} HCP(s). Skipping seed.")
    except Exception as e:
        logger.error(f"Error during database seeding: {e}")
    finally:
        db.close()

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} is ready.")

    yield  # ← application runs here

    # --- Shutdown ---
    logger.info("Shutting down...")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-First CRM backend for managing Healthcare Professional (HCP) "
        "interactions. Features a LangGraph-powered conversational agent "
        "for logging, searching, and analysing HCP engagements."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

app.include_router(interactions_router)
app.include_router(hcp_router)
app.include_router(agent_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint — basic health check.

    Returns application name, version, status, and current server time.
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Detailed health check endpoint.

    Verifies database connectivity and reports Groq API key status.
    """
    db_status = "connected"
    try:
        db = get_db_session()
        db.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    groq_configured = bool(settings.GROQ_API_KEY)

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "groq_api_configured": groq_configured,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Run with uvicorn when executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
