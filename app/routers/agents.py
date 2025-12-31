from uuid import UUID
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from ..models.agent import Agent, AgentPublic, AgentCreate, AgentUpdate
from ..database import SessionDep

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/",
    response_model=AgentPublic,
    summary="Create a new agent",
    description="Creates a new agent and returns the public agent data.",
    responses={
        201: {
            "description": "Agent successfully created"
        }
    },
)
def create_agent(agent: AgentCreate, session: SessionDep):
    db_agent = Agent.model_validate(agent)
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)
    return db_agent


@router.get(
    "/",
    response_model=list[AgentPublic],
    summary="List agents",
    description="Retrieve a list of all agents.",
    responses={
        200: {
            "description": "List of agents returned"
        }
    },
)
def read_agents(session: SessionDep):
    agents = session.exec(select(Agent)).all()
    return agents


@router.get(
    "/{agent_id}",
    response_model=AgentPublic,
    summary="Get agent by ID",
    description="Retrieve a single agent using its UUID.",
    responses={
        200: {
            "description": "Agent found"
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent not found"}
                }
            },
        },
    },
)
def read_agent(agent_id: UUID, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch(
    "/{agent_id}",
    response_model=AgentPublic,
    summary="Update agent",
    description="Partially update an agent. Only provided fields are updated.",
    responses={
        200: {
            "description": "Agent successfully updated"
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent not found"}
                }
            },
        },
    },
)
def update_agent(agent_id: UUID, agent: AgentUpdate, session: SessionDep):
    agent_db = session.get(Agent, agent_id)
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent_data = agent.model_dump(exclude_unset=True)
    agent_db.sqlmodel_update(agent_data)
    session.add(agent_db)
    session.commit()
    session.refresh(agent_db)
    return agent_db


@router.delete(
    "/{agent_id}",
    summary="Delete agent",
    description="Delete an agent by its UUID.",
    responses={
        200: {
            "description": "Agent successfully deleted",
            "content": {
                "application/json": {
                    "example": {"ok": True}
                }
            },
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent not found"}
                }
            },
        },
    },
)
def delete_agent(agent_id: UUID, session: SessionDep):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    session.delete(agent)
    session.commit()
    return {"ok": True}
