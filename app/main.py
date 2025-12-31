from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .routers import agents

app = FastAPI(
    title="AI Agent Platform Backend API",
    description="A backend API for a platform that enables users to create, manage, and interact with AI agents via text and voice.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    create_db_and_tables()
    yield


app.router.lifespan_context = lifespan(fastapi_app=app)
app.include_router(agents.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent Platform!"}
