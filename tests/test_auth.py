from werkzeug.exceptions import HTTPException
import pytest
from backend.apis.auth import *
from tests.conftest import USER1_ID
import datetime
import jwt


def create_token(key: str, public_id: str, expired: bool = False):
    if expired:
        expire_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            1
        )
    else:
        expire_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            1
        )
    return jwt.encode(
        {"public_id": public_id, "exp": expire_date}, key, algorithm="HS256"
    )


def test_get_user_from_token_valid(app):
    with app.app_context():
        token = create_token(app.config["SECRET_KEY"], USER1_ID)
        user = get_user_from_token(token)
        assert user.public_id == USER1_ID


@pytest.mark.parametrize(
    ("public_id", "expired"), [(USER1_ID, True), ("wrong_id", False)]
)
def test_get_user_from_token_invalid(app, public_id, expired):
    with app.app_context():
        token = create_token(app.config["SECRET_KEY"], public_id, expired=expired)
        user = get_user_from_token(token)
        assert user is None


def test_token_required_token_valid(app):
    @token_required
    def inner():
        return "success"

    with app.app_context():
        token = create_token(app.secret_key, USER1_ID)
    with app.test_request_context(headers={"x-access-token": token}):
        result = inner()
        assert result == "success"


def test_token_required_token_invalid(app):
    @token_required
    def inner():
        return "success"

    with app.app_context():
        token = create_token(app.secret_key, USER1_ID, expired=True)
    with app.test_request_context(headers={"x-access-token": token}):
        with pytest.raises(HTTPException) as e:
            inner()
        assert e.value.code == 401


def test_token_required_token_missing(app):
    @token_required
    def inner():
        return "success"

    with app.test_request_context():
        with pytest.raises(HTTPException) as e:
            inner()
        assert e.value.code == 400


def test_role_required_allowed(app):
    @roles_required([Role.USER1])
    def inner():
        return "success"

    with app.app_context():
        token = create_token(app.secret_key, USER1_ID)
    with app.test_request_context(headers={"x-access-token": token}):
        result = inner()
        assert result == "success"


def test_role_required_denied(app):
    @roles_required([Role.ADMIN])
    def inner():
        return "success"

    with app.app_context():
        token = create_token(app.secret_key, USER1_ID)
    with app.test_request_context(headers={"x-access-token": token}):
        with pytest.raises(HTTPException) as e:
            inner()
        assert e.value.code == 403


@pytest.mark.parametrize(
    ["name", "password", "code"],
    [
        ("admin", "admin", 200),
        ("user1", "user1", 200),
        ("user1", "wrong_password", 400),
    ],
)
def test_login(client, name, password, code):
    response = client.login(name, password)
    assert response.status_code == code
    if code == 200:
        assert "token" in response.get_json()


def test_login_source(client):
    response = client.login("device1", "source", source=True)
    assert response.status_code == 200
    assert "token" in response.get_json()


def test_create_basic_auth_response_valid(app):
    with app.app_context():
        login_data = {"name": "user1", "password": "user1"}
        response = create_basic_auth_login_response(login_data)
        assert "token" in response


def test_create_basic_auth_response_cookie(app):
    with app.app_context():
        login_data = {"name": "user1", "password": "user1", "use_cookie": True}
        response = create_basic_auth_login_response(login_data)
        assert response.status_code == 200
    # check for token in cookie


@pytest.mark.parametrize(
    ("name", "password"), [("user1", "wrong_password"), ("wrong_user", "user1")]
)
def test_create_basic_auth_response_invalid(app, name, password):
    with app.app_context():
        login_data = {"name": name, "password": password}
        response = create_basic_auth_login_response(login_data)
        assert response is None
