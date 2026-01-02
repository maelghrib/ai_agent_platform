import logging
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.agent import Agent, AgentPublic, AgentCreate, AgentUpdate
from ..database import SessionDep

router = APIRouter(tags=["agents"])

logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=AgentPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Creates a new agent and returns the public agent data.",
    responses={
        201: {"description": "Agent successfully created"},
        500: {"description": "Database error"},
    },
)
def create_agent(agent: AgentCreate, session: SessionDep):
    try:
        logger.info("Creating agent with name='%s'", agent.name)

        db_agent = Agent.model_validate(agent)
        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)

        logger.info("Agent created successfully (id=%s)", db_agent.id)
        return db_agent

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception("Database error while creating agent")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent",
        ) from e


@router.get(
    "/",
    response_model=list[AgentPublic],
    status_code=status.HTTP_200_OK,
    summary="List agents",
    description="Retrieve a list of all agents.",
    responses={
        200: {"description": "List of agents returned"},
        500: {"description": "Database error"},
    },
)
def read_agents(session: SessionDep):
    try:
        logger.debug("Fetching list of agents")

        agents = session.exec(select(Agent)).all()

        logger.info("Retrieved %d agents", len(agents))
        return agents

    except SQLAlchemyError as e:
        logger.exception("Database error while listing agents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents",
        ) from e


@router.get(
    "/{agent_id}",
    response_model=AgentPublic,
    status_code=status.HTTP_200_OK,
    summary="Get agent by ID",
    description="Retrieve a single agent using its UUID.",
    responses={
        200: {"description": "Agent found"},
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent not found"}
                }
            },
        },
        500: {"description": "Database error"},
    },
)
def read_agent(agent_id: str, session: SessionDep):
    try:
        logger.debug("Fetching agent id=%s", agent_id)

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info("Agent not found (id=%s)", agent_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        logger.info("Agent retrieved successfully (id=%s)", agent_id)
        return agent

    except SQLAlchemyError as e:
        logger.exception("Database error while retrieving agent id=%s", agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent",
        ) from e


@router.patch(
    "/{agent_id}",
    response_model=AgentPublic,
    status_code=status.HTTP_200_OK,
    summary="Update agent",
    description="Partially update an agent. Only provided fields are updated.",
    responses={
        200: {"description": "Agent successfully updated"},
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent not found"}
                }
            },
        },
        500: {"description": "Database error"},
    },
)
def update_agent(agent_id: str, agent: AgentUpdate, session: SessionDep):
    try:
        logger.debug("Updating agent id=%s", agent_id)

        agent_db = session.get(Agent, agent_id)
        if not agent_db:
            logger.info("Agent not found for update (id=%s)", agent_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        agent_data = agent.model_dump(exclude_unset=True)

        if not agent_data:
            logger.debug("No fields provided for update (id=%s)", agent_id)
            return agent_db

        agent_db.sqlmodel_update(agent_data)

        session.add(agent_db)
        session.commit()
        session.refresh(agent_db)

        logger.info("Agent updated successfully (id=%s)", agent_id)
        return agent_db

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception("Database error while updating agent id=%s", agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent",
        ) from e


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_200_OK,
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
        500: {"description": "Database error"},
    },
)
def delete_agent(agent_id: str, session: SessionDep):
    try:
        logger.debug("Deleting agent id=%s", agent_id)

        agent = session.get(Agent, agent_id)
        if not agent:
            logger.info("Agent not found for deletion (id=%s)", agent_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        session.delete(agent)
        session.commit()

        logger.info("Agent deleted successfully (id=%s)", agent_id)
        return {"ok": True}

    except SQLAlchemyError as e:
        session.rollback()
        logger.exception("Database error while deleting agent id=%s", agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent",
        ) from e
