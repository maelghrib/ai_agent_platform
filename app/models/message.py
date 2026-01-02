import uuid
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_session import ChatSession


def generate_message_id() -> str:
    return uuid.uuid4().hex


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class MessageBase(SQLModel):
    role: MessageRole = Field(default=MessageRole.user)
    content: str = Field()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(MessageBase, table=True):
    id: str = Field(default_factory=generate_message_id, primary_key=True)
    chat_session_id: str = Field(foreign_key="chat_session.id")
    chat_session: Optional["ChatSession"] = Relationship(back_populates="messages")


class MessagePublic(MessageBase):
    id: str
    chat_session_id: str


class MessageCreate(MessageBase):
    pass
