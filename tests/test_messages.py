import pytest
from app.models.agent import Agent
from app.models.chat_session import ChatSession


@pytest.fixture
def mock_agent_response(monkeypatch):
    async def fake_response(*args, **kwargs):
        return "Mocked agent response"

    monkeypatch.setattr(
        "app.routers.messages.get_openai_agent_response",
        fake_response,
    )


def test_send_message_success(
        client,
        create_test_db,
        session_override,
        mock_agent_response,
):
    agent = Agent(
        id="agent_1",
        name="Test Agent",
        instructions="You are helpful",
    )
    chat_session = ChatSession(
        id="chat_1",
        agent_id="agent_1",
    )

    session_override.add(agent)
    session_override.add(chat_session)
    session_override.commit()

    response = client.post(
        "/agents/agent_1/chat_sessions/chat_1/messages",
        json={"role": "user", "content": "Hello"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["role"] == "assistant"
    assert data["content"] == "Mocked agent response"
