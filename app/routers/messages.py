import os
import logging
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent as OpenAIAgent,
    Runner,
    SQLiteSession,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from ..models.agent import Agent
from ..models.chat_session import ChatSession
from ..models.message import Message, MessagePublic, MessageCreate, MessageRole
from ..database import SessionDep

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(tags=["messages"])


async def get_chat_session_history(chat_session: ChatSession):
    """
    Retrieve the chat session history and populate it into a SQLiteSession object.

    Args:
        chat_session (ChatSession): The chat session object.

    Returns:
        SQLiteSession: Populated session history.
    """
    try:
        logger.debug("Initializing chat session history for session_id=%s", chat_session.id)

        chat_session_history = SQLiteSession(session_id=chat_session.id)

        chat_session_messages = []
        for chat_session_message in chat_session.messages:
            chat_session_messages.append({
                "content": chat_session_message.content,
                "role": chat_session_message.role
            })

        if chat_session_messages:
            await chat_session_history.add_items(chat_session_messages)
            logger.info(
                "Added %d messages to chat session history (session_id=%s)",
                len(chat_session_messages),
                chat_session.id,
            )
        else:
            logger.info("No messages found for chat session (session_id=%s)", chat_session.id)

        return chat_session_history

    except Exception as e:
        logger.exception("Failed to retrieve chat session history (session_id=%s)", chat_session.id)
        raise RuntimeError("Unable to get chat session history") from e


async def get_openai_agent_response(
        db_agent: Agent,
        user_message: str,
        chat_session_history: SQLiteSession
) -> str:
    """
    Generate a response from the OpenAI agent for a given user message and chat session.

    Args:
        db_agent (Agent): The agent object from the database.
        user_message (str): The user input message.
        chat_session_history (SQLiteSession): Chat session history.

    Returns:
        str: The agent's response text.
    """
    try:
        logger.debug("Preparing OpenAI agent response for agent_id=%s", db_agent.id)

        base_url = os.getenv("BASE_URL")
        api_key = os.getenv("API_KEY")
        model_name = os.getenv("MODEL_NAME")

        if not all([base_url, api_key, model_name]):
            missing = [name for name, val in [("BASE_URL", base_url), ("API_KEY", api_key), ("MODEL_NAME", model_name)]
                       if not val]
            logger.error("Missing environment variables: %s", missing)
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        set_default_openai_client(client=client, use_for_tracing=False)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(disabled=True)

        openai_agent = OpenAIAgent(
            name=db_agent.name,
            instructions=db_agent.instructions,
            model=model_name,
        )

        openai_agent_response = await Runner.run(
            starting_agent=openai_agent,
            input=user_message,
            session=chat_session_history
        )

        logger.info("Generated OpenAI response for agent_id=%s", db_agent.id)
        return str(openai_agent_response.final_output)

    except Exception as e:
        logger.exception("Failed to generate OpenAI agent response for agent_id=%s", db_agent.id)
        raise RuntimeError("OpenAI agent response generation failed") from e


import logging
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=MessagePublic,
    status_code=status.HTTP_200_OK,
    summary="Send a message to an agent",
    description="""
Send a user message to an AI agent within a chat session.

The system will:
1. Store the user message
2. Load chat history
3. Generate an AI response using the agent
4. Store and return the AI response
""",
    responses={
        404: {"description": "Agent or Chat Session not found"},
        500: {"description": "Internal server error"},
    },
)
async def send_message(agent_id: str, chat_session_id: str, message: MessageCreate, session: SessionDep):
    try:
        logger.debug("Sending message to agent_id=%s, chat_session_id=%s", agent_id, chat_session_id)

        db_agent = session.get(Agent, agent_id)
        if not db_agent:
            logger.info("Agent not found (id=%s)", agent_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        chat_session = session.exec(
            select(ChatSession)
            .where(ChatSession.id == chat_session_id)
            .where(ChatSession.agent_id == agent_id)
        ).first()
        if not chat_session:
            logger.info("Chat session not found (id=%s) for agent_id=%s", chat_session_id, agent_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

        db_user_message = Message(
            role=MessageRole.user,
            content=message.content,
            chat_session_id=chat_session.id,
        )
        session.add(db_user_message)
        session.commit()
        session.refresh(db_user_message)
        logger.info(
            "User message stored (message_id=%s) in chat_session_id=%s", db_user_message.id, chat_session.id
        )

        chat_session_history = await get_chat_session_history(chat_session=chat_session)

        openai_agent_response = await get_openai_agent_response(
            db_agent=db_agent,
            user_message=message.content,
            chat_session_history=chat_session_history
        )
        logger.info(
            "OpenAI agent response generated for agent_id=%s, chat_session_id=%s",
            agent_id,
            chat_session.id
        )

        db_agent_response_message = Message(
            role=MessageRole.assistant,
            content=openai_agent_response,
            chat_session_id=chat_session.id,
        )
        session.add(db_agent_response_message)
        session.commit()
        session.refresh(db_agent_response_message)
        logger.info(
            "AI response message stored (message_id=%s) in chat_session_id=%s",
            db_agent_response_message.id,
            chat_session.id
        )

        return db_agent_response_message

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception(
            "Database error while sending message to agent_id=%s, chat_session_id=%s",
            agent_id,
            chat_session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store or retrieve messages"
        ) from e

    except Exception as e:
        logger.exception(
            "Unexpected error while sending message to agent_id=%s, chat_session_id=%s",
            agent_id,
            chat_session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        ) from e
