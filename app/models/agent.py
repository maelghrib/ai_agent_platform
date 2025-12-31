import uuid
from sqlmodel import Field, SQLModel, Relationship
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_session import ChatSession


def generate_agent_id() -> str:
    return uuid.uuid4().hex


class AgentBase(SQLModel):
    name: str = Field()
    instructions: str = Field()


class Agent(AgentBase, table=True):
    id: str = Field(default_factory=generate_agent_id, primary_key=True)
    chat_sessions: List["ChatSession"] = Relationship(back_populates="agent")


class AgentPublic(AgentBase):
    id: str


class AgentCreate(AgentBase):
    pass


class AgentUpdate(AgentBase):
    name: str | None = None
    instructions: str | None = None
