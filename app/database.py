import logging
from typing import Annotated
from fastapi import Depends, HTTPException
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

sqlite_file_name = "ai_agent_platform.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(
    sqlite_url,
    connect_args=connect_args,
    echo=False,
)


def create_db_and_tables() -> None:
    try:
        logger.info("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except SQLAlchemyError as e:
        logger.exception("Database initialization failed.")
        raise RuntimeError("Failed to initialize database") from e


def get_session():
    try:
        with Session(engine) as session:
            yield session
    except SQLAlchemyError as e:
        logger.exception("Database session error.")
        raise HTTPException(
            status_code=500,
            detail="Database error",
        ) from e
    finally:
        logger.debug("Database session closed.")


SessionDep = Annotated[Session, Depends(get_session)]
