import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from .database import create_db_and_tables
from .routers import agents, chat_sessions, messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting application...")
        create_db_and_tables()
        logger.info("Database initialized successfully.")
        yield
    except Exception as e:
        logger.exception("Application startup failed.")
        raise e
    finally:
        logger.info("Shutting down application...")


app = FastAPI(
    title="AI Agent Platform Backend API",
    description="A backend API for a platform that enables users to create, manage, and interact with AI agents via text and voice.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation failed",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
        },
    )


app.include_router(
    router=agents.router,
    prefix="/agents"
)
app.include_router(
    router=chat_sessions.router,
    prefix="/agents/{agent_id}/chat_sessions"
)
app.include_router(
    router=messages.router,
    prefix="/agents/{agent_id}/chat_sessions/{chat_session_id}/messages"
)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent Platform!"}
