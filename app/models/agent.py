import uuid
from sqlmodel import Field, SQLModel


def generate_agent_id() -> str:
    return uuid.uuid4().hex


class AgentBase(SQLModel):
    name: str = Field()
    instructions: str = Field()


class Agent(AgentBase, table=True):
    id: str = Field(default_factory=generate_agent_id, primary_key=True)


class AgentPublic(AgentBase):
    id: str


class AgentCreate(AgentBase):
    pass


class AgentUpdate(AgentBase):
    name: str | None = None
    instructions: str | None = None
