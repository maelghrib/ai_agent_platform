from fastapi import FastAPI
from .database import create_db_and_tables
from .routers import agents

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(agents.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent Platform!"}
