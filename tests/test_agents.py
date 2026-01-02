from uuid import uuid4

create_agent_input = {
    "name": "Footbal Agent",
    "instructions": "You are an agent who helps in answering football questions"
}

update_agent_input = {
    "name": "Updated Footbal Agent",
    "instructions": "You are an updated agent who helps in answering football questions"
}


def test_create_agent(client):
    response = client.post(
        "/agents",
        json=create_agent_input
    )

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["name"] == create_agent_input["name"]
    assert data["instructions"] == create_agent_input["instructions"]


def test_read_agents(client):
    response = client.get("/agents")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_agent_by_id(client):
    create = client.post(
        "/agents",
        json=create_agent_input
    )
    agent_id = create.json()["id"]

    response = client.get(f"/agents/{agent_id}")

    assert response.status_code == 200
    assert response.json()["name"] == create_agent_input["name"]


def test_read_agent_not_found(client):
    response = client.get(f"/agents/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"


def test_update_agent(client):
    create = client.post(
        "/agents",
        json=update_agent_input,
    )
    agent_id = create.json()["id"]

    response = client.patch(
        f"/agents/{agent_id}",
        json=update_agent_input,
    )

    assert response.status_code == 200
    assert response.json()["name"] == update_agent_input["name"]
    assert response.json()["instructions"] == update_agent_input["instructions"]


def test_update_agent_no_fields(client):
    create = client.post("/agents", json=create_agent_input)
    agent_id = create.json()["id"]

    response = client.patch(f"/agents/{agent_id}", json={})
    assert response.status_code == 200
    assert response.json()["name"] == create_agent_input["name"]
    assert response.json()["instructions"] == create_agent_input["instructions"]


def test_update_agent_not_found(client):
    response = client.delete(f"/agents/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"


def test_delete_agent(client):
    create = client.post(
        "/agents",
        json=update_agent_input,
    )
    agent_id = create.json()["id"]

    response = client.delete(f"/agents/{agent_id}")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_delete_agent_not_found(client):
    response = client.delete(f"/agents/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"
