from fastapi import FastAPI
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


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(agents.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent Platform!"}
