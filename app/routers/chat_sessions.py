import logging
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select, func

from ..models.agent import Agent
from ..models.chat_session import ChatSession, ChatSessionPublic, ChatSessionCreate, ChatSessionUpdate
from ..database import SessionDep

router = APIRouter(tags=["chat_sessions"])

logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=ChatSessionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
    description=(
            "Create a new chat session for a specific agent. "
            "If no name is provided, the session will be named automatically "
            "as `Chat N` where N is the next session number for that agent."
    ),
    responses={
        201: {"description": "Chat session created successfully"},
        404: {"description": "Agent not found"},
        500: {"description": "Database error"},
    },
)
def create_chat_session(
        agent_id: str,
        chat_session: ChatSessionCreate,
        session: SessionDep,
):
    try:
        logger.debug("Creating chat session for agent_id=%s", agent_id)

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info("Agent not found when creating chat session (id=%s)", agent_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        count = session.exec(
            select(func.count())
            .select_from(ChatSession)
            .where(ChatSession.agent_id == agent_id)
        ).one()

        db_chat_session = ChatSession(
            agent_id=agent_id,
            name=chat_session.name or f"Chat {count + 1}",
        )

        session.add(db_chat_session)
        session.commit()
        session.refresh(db_chat_session)

        logger.info(
            "Chat session created successfully (id=%s, agent_id=%s)",
            db_chat_session.id,
            agent_id,
        )
        return db_chat_session

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(
            "Database error while creating chat session for agent_id=%s",
            agent_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session",
        ) from e


@router.get(
    "/",
    response_model=list[ChatSessionPublic],
    status_code=status.HTTP_200_OK,
    summary="List chat sessions",
    description="Retrieve all chat sessions belonging to a specific agent.",
    responses={
        200: {"description": "List of chat sessions"},
        404: {"description": "Agent not found"},
        500: {"description": "Database error"},
    },
)
def read_chat_sessions(agent_id: str, session: SessionDep):
    try:
        logger.debug("Fetching chat sessions for agent_id=%s", agent_id)

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info("Agent not found when listing chat sessions (id=%s)", agent_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        chat_sessions = session.exec(
            select(ChatSession).where(ChatSession.agent_id == agent_id)
        ).all()

        logger.info(
            "Retrieved %d chat sessions for agent_id=%s",
            len(chat_sessions),
            agent_id,
        )
        return chat_sessions

    except SQLAlchemyError as e:
        logger.exception(
            "Database error while retrieving chat sessions for agent_id=%s",
            agent_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions",
        ) from e


@router.get(
    "/{chat_session_id}",
    response_model=ChatSessionPublic,
    status_code=status.HTTP_200_OK,
    summary="Get a chat session",
    description="Retrieve a single chat session by its ID, scoped to an agent.",
    responses={
        200: {"description": "Chat session found"},
        404: {"description": "Agent or chat session not found"},
        500: {"description": "Database error"},
    },
)
def read_chat_session(agent_id: str, chat_session_id: str, session: SessionDep):
    try:
        logger.debug(
            "Fetching chat session id=%s for agent_id=%s",
            chat_session_id,
            agent_id,
        )

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info("Agent not found when fetching chat session (id=%s)", agent_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        chat_session = session.exec(
            select(ChatSession)
            .where(ChatSession.id == chat_session_id)
            .where(ChatSession.agent_id == agent_id)
        ).first()

        if not chat_session:
            logger.info(
                "Chat session not found (id=%s) for agent_id=%s",
                chat_session_id,
                agent_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

        logger.info(
            "Chat session retrieved successfully (id=%s) for agent_id=%s",
            chat_session_id,
            agent_id,
        )
        return chat_session

    except SQLAlchemyError as e:
        logger.exception(
            "Database error while fetching chat session id=%s for agent_id=%s",
            chat_session_id,
            agent_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session",
        ) from e


@router.patch(
    "/{chat_session_id}",
    response_model=ChatSessionPublic,
    status_code=status.HTTP_200_OK,
    summary="Update a chat session",
    description="Partially update a chat session. Only provided fields are updated.",
    responses={
        200: {"description": "Chat session updated successfully"},
        404: {"description": "Agent or chat session not found"},
        500: {"description": "Database error"},
    },
)
def update_chat_session(
        agent_id: str,
        chat_session_id: str,
        chat_session: ChatSessionUpdate,
        session: SessionDep,
):
    try:
        logger.debug(
            "Updating chat session id=%s for agent_id=%s",
            chat_session_id,
            agent_id,
        )

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info(
                "Agent not found when updating chat session (id=%s)", agent_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        chat_session_db = session.exec(
            select(ChatSession)
            .where(ChatSession.id == chat_session_id)
            .where(ChatSession.agent_id == agent_id)
        ).first()

        if not chat_session_db:
            logger.info(
                "Chat session not found (id=%s) for agent_id=%s",
                chat_session_id,
                agent_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

        chat_session_data = chat_session.model_dump(exclude_unset=True)
        if not chat_session_data:
            logger.debug(
                "No fields provided for update (chat_session_id=%s)", chat_session_id
            )
            return chat_session_db

        chat_session_db.sqlmodel_update(chat_session_data)

        session.add(chat_session_db)
        session.commit()
        session.refresh(chat_session_db)

        logger.info(
            "Chat session updated successfully (id=%s) for agent_id=%s",
            chat_session_id,
            agent_id,
        )
        return chat_session_db

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(
            "Database error while updating chat session id=%s for agent_id=%s",
            chat_session_id,
            agent_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat session",
        ) from e


@router.delete(
    "/{chat_session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat session",
    description="Delete a chat session belonging to a specific agent.",
    responses={
        200: {
            "description": "Chat session deleted successfully",
            "content": {"application/json": {"example": {"ok": True}}},
        },
        404: {"description": "Agent or chat session not found"},
        500: {"description": "Database error"},
    },
)
def delete_chat_session(agent_id: str, chat_session_id: str, session: SessionDep):
    try:
        logger.debug(
            "Deleting chat session id=%s for agent_id=%s",
            chat_session_id,
            agent_id,
        )

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info(
                "Agent not found when deleting chat session (id=%s)", agent_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        chat_session = session.exec(
            select(ChatSession)
            .where(ChatSession.id == chat_session_id)
            .where(ChatSession.agent_id == agent_id)
        ).first()

        if not chat_session:
            logger.info(
                "Chat session not found (id=%s) for agent_id=%s",
                chat_session_id,
                agent_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

        session.delete(chat_session)
        session.commit()

        logger.info(
            "Chat session deleted successfully (id=%s) for agent_id=%s",
            chat_session_id,
            agent_id,
        )
        return {"ok": True}

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(
            "Database error while deleting chat session id=%s for agent_id=%s",
            chat_session_id,
            agent_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session",
        ) from e
