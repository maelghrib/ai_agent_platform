def create_agent(client):
    response = client.post(
        "/agents/",
        json={
            "name": "Footbal Agent",
            "instructions": "You are an agent who helps in answering football questions"
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_create_chat_session(client):
    agent_id = create_agent(client)

    response = client.post(
        f"/agents/{agent_id}/chat_sessions/",
        json={},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Chat 1"
    assert data["agent_id"] == agent_id


def test_chat_session_name_increment(client):
    agent_id = create_agent(client)

    client.post(f"/agents/{agent_id}/chat_sessions/", json={})
    response = client.post(f"/agents/{agent_id}/chat_sessions/", json={})

    assert response.json()["name"] == "Chat 2"


def test_read_chat_sessions(client):
    agent_id = create_agent(client)

    client.post(f"/agents/{agent_id}/chat_sessions/", json={})
    client.post(f"/agents/{agent_id}/chat_sessions/", json={})

    response = client.get(f"/agents/{agent_id}/chat_sessions/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_read_chat_session(client):
    agent_id = create_agent(client)

    create_response = client.post(
        f"/agents/{agent_id}/chat_sessions/",
        json={},
    )
    chat_session_id = create_response.json()["id"]

    response = client.get(
        f"/agents/{agent_id}/chat_sessions/{chat_session_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == chat_session_id


def test_update_chat_session(client):
    agent_id = create_agent(client)

    create_response = client.post(
        f"/agents/{agent_id}/chat_sessions/",
        json={},
    )
    chat_session_id = create_response.json()["id"]

    response = client.patch(
        f"/agents/{agent_id}/chat_sessions/{chat_session_id}",
        json={"name": "Updated Chat"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Chat"


def test_delete_chat_session(client):
    agent_id = create_agent(client)

    create_response = client.post(
        f"/agents/{agent_id}/chat_sessions/",
        json={},
    )
    chat_session_id = create_response.json()["id"]

    response = client.delete(
        f"/agents/{agent_id}/chat_sessions/{chat_session_id}"
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_create_chat_session_agent_not_found(client):
    response = client.post(
        "/agents/invalid-agent-id/chat_sessions/",
        json={},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"


def test_read_chat_session_not_found(client):
    agent_id = create_agent(client)

    response = client.get(
        f"/agents/{agent_id}/chat_sessions/invalid-session-id"
    )

    assert response.status_code == 404
