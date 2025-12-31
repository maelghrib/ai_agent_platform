from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from ..models.agent import Agent
from ..models.chat_session import ChatSession, ChatSessionPublic, ChatSessionCreate, ChatSessionUpdate
from ..database import SessionDep

router = APIRouter(tags=["chat_sessions"])


@router.post("/", response_model=ChatSessionPublic)
def create_chat_session(agent_id: str, chat_session: ChatSessionCreate, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    count = session.exec(
        select(func.count())
        .select_from(ChatSession)
        .where(ChatSession.agent_id == agent_id)
    ).one()

    db_chat_session = ChatSession(
        agent_id=agent_id,
        name=chat_session.name or f"Chat {count + 1}"
    )

    session.add(db_chat_session)
    session.commit()
    session.refresh(db_chat_session)
    return db_chat_session


@router.get("/", response_model=list[ChatSessionPublic])
def read_chat_sessions(agent_id: str, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    chat_sessions = session.exec(select(ChatSession).where(ChatSession.agent_id == agent_id)).all()
    return chat_sessions


@router.get("/{chat_session_id}", response_model=ChatSessionPublic)
def read_chat_session(agent_id: str, chat_session_id: str, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    chat_session = session.exec(
        select(ChatSession)
        .where(ChatSession.id == chat_session_id)
        .where(ChatSession.agent_id == agent_id)
    ).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat_session


@router.patch("/{chat_session_id}", response_model=ChatSessionPublic)
def update_chat_session(agent_id: str, chat_session_id: str, chat_session: ChatSessionUpdate, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    chat_session_db = session.exec(
        select(ChatSession)
        .where(ChatSession.id == chat_session_id)
        .where(ChatSession.agent_id == agent_id)
    ).first()
    if not chat_session_db:
        raise HTTPException(status_code=404, detail="Chat session not found")
    chat_session_data = chat_session.model_dump(exclude_unset=True)
    chat_session_db.sqlmodel_update(chat_session_data)
    session.add(chat_session_db)
    session.commit()
    session.refresh(chat_session_db)
    return chat_session_db


@router.delete("/{chat_session_id}")
def delete_chat_session(agent_id: str, chat_session_id: str, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    chat_session = session.exec(
        select(ChatSession)
        .where(ChatSession.id == chat_session_id)
        .where(ChatSession.agent_id == agent_id)
    ).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    session.delete(chat_session)
    session.commit()
    return {"ok": True}
