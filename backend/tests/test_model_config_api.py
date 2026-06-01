from fastapi.testclient import TestClient


def test_create_model_config_masks_api_key(client: TestClient) -> None:
    response = client.post(
        "/api/models/configs",
        json={
            "name": "Compatible API",
            "provider": "openai-compatible",
            "base_url": "https://example.com/v1",
            "api_key": "sk-testabcd",
            "model_name": "configurable-model",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["masked_api_key"] == "sk-****abcd"
    assert data["is_default"] is True
    assert "api_key" not in data
    assert "api_key_encrypted" not in data


def test_set_default_keeps_only_one_default(client: TestClient) -> None:
    first = client.post(
        "/api/models/configs",
        json={
            "name": "First",
            "provider": "mock",
            "model_name": "mock-one",
        },
    ).json()
    second = client.post(
        "/api/models/configs",
        json={
            "name": "Second",
            "provider": "mock",
            "model_name": "mock-two",
            "is_default": True,
        },
    ).json()

    assert first["is_default"] is True
    assert second["is_default"] is True

    configs = client.get("/api/models/configs").json()
    defaults = [config for config in configs if config["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == second["id"]

    response = client.post(f"/api/models/configs/{first['id']}/set-default")
    assert response.status_code == 200
    assert response.json()["id"] == first["id"]
    assert response.json()["is_default"] is True

    configs = client.get("/api/models/configs").json()
    defaults = [config for config in configs if config["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == first["id"]


def test_model_config_test_uses_mock_provider(client: TestClient) -> None:
    config = client.post(
        "/api/models/configs",
        json={
            "name": "Mock",
            "provider": "mock",
            "model_name": "mock-model",
        },
    ).json()

    response = client.post(f"/api/models/configs/{config['id']}/test")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "OK"
    assert isinstance(data["latency_ms"], int)
