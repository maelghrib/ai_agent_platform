import uuid
from sqlmodel import Field, SQLModel


class AgentBase(SQLModel):
    name: str = Field()
    instructions: str = Field()


class Agent(AgentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class AgentPublic(AgentBase):
    id: uuid.UUID


class AgentCreate(AgentBase):
    pass


class AgentUpdate(AgentBase):
    name: str | None = None
    instructions: str | None = None
