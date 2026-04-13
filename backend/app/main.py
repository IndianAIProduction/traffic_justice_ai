import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.exceptions import AppException
from app.api.v1.router import api_router
from app.db.session import engine

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])

CHROMA_MAX_RETRIES = 5
CHROMA_RETRY_DELAY = 3


def _run_ingestion_sync():
    """Background thread: wait for ChromaDB, then ingest if needed."""
    from app.rag.ingestion import is_corpus_ingested, ingest_legal_corpus

    for attempt in range(1, CHROMA_MAX_RETRIES + 1):
        try:
            if is_corpus_ingested():
                logger.info("Legal corpus already in ChromaDB — skipping ingestion")
                return
            break
        except Exception as e:
            logger.warning(
                f"ChromaDB not ready (attempt {attempt}/{CHROMA_MAX_RETRIES}): {e}"
            )
            if attempt < CHROMA_MAX_RETRIES:
                time.sleep(CHROMA_RETRY_DELAY)
            else:
                logger.error("ChromaDB unreachable after retries — skipping auto-ingestion")
                return

    try:
        count = ingest_legal_corpus()
        logger.info(f"Auto-ingestion complete: {count} chunks stored in ChromaDB")
    except Exception as e:
        logger.error(f"Auto-ingestion failed: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"({settings.publisher_name})"
    )

    ingestion_thread = threading.Thread(target=_run_ingestion_sync, daemon=True)
    ingestion_thread.start()
    logger.info("Background legal corpus ingestion started")

    yield
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-Powered Legal Transparency Platform for Indian Drivers. "
        f"Publisher: {settings.publisher_name}. "
        f"Website: {settings.publisher_url} · YouTube: {settings.publisher_youtube_url}"
    ),
    contact={
        "name": settings.publisher_name,
        "url": settings.publisher_url,
    },
    license_info={
        "name": "Proprietary — see LICENSE file in the repository",
        "url": settings.publisher_url,
    },
    lifespan=lifespan,
    redirect_slashes=False,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "publisher": settings.publisher_name,
        "publisher_url": settings.publisher_url,
        "publisher_youtube_url": settings.publisher_youtube_url,
    }


app.include_router(api_router)
