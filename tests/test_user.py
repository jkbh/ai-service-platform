from tests.conftest import USER1_ID


def test_post_user(client):
    client.login("admin", "admin")

    response = client.post(
        "/user",
        json={"name": "test-user", "password": "test-password", "role": "user1"},
    )

    assert response.status_code == 201
    assert "public_id" in response.get_json()
    assert "password" not in response.get_json()

    # invalid input data
    response = client.post("/user", json={"name": "test-user", "role": "user1"})

    assert response.status_code == 422


def test_get_all_users(client):
    client.login("admin", "admin")

    response = client.get("/user")

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_user(client):
    client.login("admin", "admin")

    response = client.get(f"/user/{USER1_ID}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "user1"

    # non existing user
    response = client.get("/user/fake_id")

    assert response.status_code == 404


def test_delete_user(client):
    client.login("admin", "admin")

    response = client.delete(f"/user/{USER1_ID}")

    assert response.status_code == 200
    assert "public_id" in response.get_json()

    # deleted user should not be found
    response = client.delete(f"/user/{USER1_ID}")

    assert response.status_code == 404
