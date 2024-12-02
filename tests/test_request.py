from tests.conftest import (
    BYTE_IMAGE,
    USER1_REQ_ID,
    CLASSIFIER_ID,
    MOBILENET_ID,
    USER1_ID,
    USER2_ID,
)
from time import sleep
import base64
import pytest


@pytest.mark.parametrize(
    ("name", "user_id"), [("user1", USER1_ID), ("user2", USER2_ID)]
)
def test_get_request_list_user(client, name, user_id):
    client.login(name, name)

    response = client.get("/request")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["user_id"] == user_id


def test_get_request_list_admin(client):
    client.login("admin", "admin")

    response = client.get("/request")

    assert response.status_code == 200
    assert len(response.get_json()) == 2


@pytest.mark.parametrize(
    ("name", "request_id", "code"),
    [
        ("user1", USER1_REQ_ID, 200),
        ("user2", USER1_REQ_ID, 403),
        ("user1", "wrong_id", 404),
    ],
)
def test_get_request_invalid(client, name, request_id, code):
    client.login(name, name)

    response = client.get(f"/request/{request_id}")
    assert response.status_code == code
    if code == 200:
        assert "output" in response.get_json()


@pytest.mark.parametrize(
    ("name", "model_id", "code"),
    [
        ("user1", CLASSIFIER_ID, 201),
        ("user1", MOBILENET_ID, 201),
        ("user1", "wrong_id", 404),
    ],
)
def test_post_request_custom(client, name, model_id, code):
    client.login(name, name)

    response = client.post(
        "/request",
        json={
            "model_id": model_id,
            "input": base64.b64encode(BYTE_IMAGE).decode("utf-8"),
        },
    )

    assert response.status_code == code
    if response.status_code == 201:
        assert "status" in response.get_json()
        sleep(3)


@pytest.mark.parametrize(
    ("name", "password", "request_id", "code"),
    [
        ("user2", "user2", USER1_REQ_ID, 403),
        ("user1", "user1", USER1_REQ_ID, 200),
        ("user1", "user1", "wrong_id", 404),
    ],
)
def test_delete_request(client, name, password, request_id, code):
    client.login(name, password)

    response = client.delete(f"/request/{request_id}")

    assert response.status_code == code
    if code == 200:
        assert "public_id" in response.get_json()
