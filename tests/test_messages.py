import io
import pytest
import tempfile
from unittest.mock import patch, AsyncMock
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


def test_send_text_message_success(
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
        "/agents/agent_1/chat_sessions/chat_1/messages/text",
        json={"content": "Hello"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["role"] == "assistant"
    assert data["content"] == "Mocked agent response"


def test_send_voice_message_success(
        client,
        create_test_db,
        session_override
):
    agent = Agent(
        id="voice_agent_1",
        name="Test Agent",
        instructions="You are helpful",
    )
    chat_session = ChatSession(
        id="voice_chat_1",
        agent_id="voice_agent_1",
    )
    session_override.add(agent)
    session_override.add(chat_session)
    session_override.commit()

    audio_content = b"fake audio content"
    fake_file = io.BytesIO(audio_content)
    fake_file.name = "test_audio.wav"

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio_file:
        tmp_audio_file.write(b"fake TTS audio content")
        tmp_audio_file_path = tmp_audio_file.name

    with patch("app.routers.messages.convert_speech_to_text", new_callable=AsyncMock) as mock_speech_to_text, \
            patch("app.routers.messages.get_chat_session_history", new_callable=AsyncMock) as mock_history, \
            patch("app.routers.messages.get_openai_agent_response", new_callable=AsyncMock) as mock_agent_response, \
            patch("app.routers.messages.convert_text_to_speech", new_callable=AsyncMock) as mock_text_to_speech:

        mock_speech_to_text.return_value = "Hello from voice"
        mock_history.return_value = []
        mock_agent_response.return_value = "Hi, this is the agent!"
        mock_text_to_speech.return_value = tmp_audio_file_path

        response = client.post(
            "/agents/voice_agent_1/chat_sessions/voice_chat_1/messages/voice",
            files={"file": ("test_audio.wav", fake_file, "audio/wav")},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert "attachment" in response.headers["content-disposition"]
        assert response.headers["content-disposition"].endswith(".mp3\"")
