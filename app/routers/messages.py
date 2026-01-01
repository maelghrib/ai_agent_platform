import os
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

router = APIRouter(tags=["messages"])


async def get_chat_session_history(chat_session: ChatSession):
    chat_session_history = SQLiteSession(session_id=chat_session.id)

    chat_session_messages = []
    for chat_session_message in chat_session.messages:
        chat_session_messages.append({
            "content": chat_session_message.content,
            "role": chat_session_message.role
        })

    await chat_session_history.add_items(chat_session_messages)

    return chat_session_history


async def get_openai_agent_response(db_agent: Agent, user_message: str, chat_session_history: SQLiteSession):
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("MODEL_NAME")

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

    return str(openai_agent_response.final_output)


@router.post("/", response_model=MessagePublic)
async def send_message(agent_id: str, chat_session_id: str, message: MessageCreate, session: SessionDep):
    db_agent = session.get(Agent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    chat_session = session.exec(
        select(ChatSession)
        .where(ChatSession.id == chat_session_id)
        .where(ChatSession.agent_id == agent_id)
    ).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db_user_message = Message(
        role=MessageRole.user,
        content=message.content,
        chat_session_id=chat_session.id,
    )
    session.add(db_user_message)
    session.commit()
    session.refresh(db_user_message)

    chat_session_history = await get_chat_session_history(chat_session=chat_session)

    openai_agent_response = await get_openai_agent_response(
        db_agent=db_agent,
        user_message=message.content,
        chat_session_history=chat_session_history
    )

    db_agent_response_message = Message(
        role=MessageRole.assistant,
        content=openai_agent_response,
        chat_session_id=chat_session.id,
    )
    session.add(db_agent_response_message)
    session.commit()
    session.refresh(db_agent_response_message)

    return db_agent_response_message
