import uuid
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent
    from .message import Message


def generate_session_id() -> str:
    return uuid.uuid4().hex


class ChatSessionBase(SQLModel):
    name: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatSession(ChatSessionBase, table=True):
    __tablename__ = "chat_session"
    id: str = Field(default_factory=generate_session_id, primary_key=True)
    agent_id: str = Field(foreign_key="agent.id")
    agent: Optional["Agent"] = Relationship(back_populates="chat_sessions")
    messages: List["Message"] = Relationship(back_populates="chat_session")


class ChatSessionPublic(ChatSessionBase):
    id: str
    agent_id: str
    messages: list


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(ChatSessionBase):
    name: str | None = None
