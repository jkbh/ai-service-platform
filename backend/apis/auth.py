from typing import Dict, Optional, List

import flask
from flask import request, current_app, g, after_this_request
from flask.json import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow_enum import EnumField
from werkzeug.security import check_password_hash
from functools import wraps

import jwt
import datetime

from backend.core.models import User, Source, Role

from . import ma

bp = Blueprint("auth", __name__, url_prefix="/auth")


class LoginArgsSchema(ma.Schema):
    name = ma.Str(required=True)
    password = ma.Str(required=True)
    source = ma.Bool()
    use_cookie = ma.Bool()


class TokenSchema(ma.Schema):
    token = ma.Str(required=True)
    role = EnumField(Role)


class StatusSchema(ma.Schema):
    name = ma.Str()
    role = EnumField(Role)


def get_user_from_token(token: str) -> Optional[User]:
    """Validates if a token is carrying a valid public_id

    Args:
        token: The token to validate

    Returns:
        The corresponding user if valid, None if invalid
    """

    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None

    # TODO: right now, a source is considered to be the same as a user -> both need a role entry,
    #  even though this does not make sense for a source
    user = Source.query.filter_by(public_id=data["public_id"]).first()
    if not user:
        user = User.query.filter_by(public_id=data["public_id"]).first()

    return user


def token_required(f):
    """Checks if a request includes a valid token.

    If a user is found, it gets added to the request context and can be accessed through the g object.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        else:
            token = request.cookies.get("token")

        if not token:
            abort(400, message="Token missing")

        user = get_user_from_token(token)

        if not user:
            abort(401, message="Invalid token")

        g.user = user

        return f(*args, **kwargs)

    return decorated


def roles_required(allowed: List[Role]):
    """Checks if current user has at least one of the allowed roles

    This decorator used the g object to read the current user.

    Args:
    allowed: A list of allowed roles. Can be any combination of user1, user2, admin, dev, source
    """

    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if g.user.role not in allowed:
                abort(403, message="Invalid token")

            return f(*args, **kwargs)

        return decorated

    return decorator


@bp.route("/login")
class Login(MethodView):
    @bp.arguments(LoginArgsSchema)
    @bp.response(200, TokenSchema)
    def post(self, data):
        response = create_basic_auth_login_response(data)

        if not response:
            abort(400, message="Could not login")

        return response


@bp.route("/status")
class Status(MethodView):
    @bp.response(200, StatusSchema)
    @token_required
    def get(self):
        return g.user


@bp.route("/logout")
class Logout(MethodView):
    @bp.response(200)
    def post(self):
        @after_this_request
        def delete_token_cookie(response):
            response.delete_cookie("token")
            return response

        return {"message": "Logged out!"}


def create_basic_auth_login_response(login_data: Dict):
    user = User.query.filter_by(name=login_data["name"]).first()
    if not user:
        user = Source.query.filter_by(name=login_data["name"]).first()

    if not user:
        return

    # hash public_id & expire date into token (currently 30 days)
    if check_password_hash(user.password, login_data["password"]):
        token = jwt.encode(
            {
                "public_id": user.public_id,
                "source": False,
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(30),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        use_cookie = login_data.get("use_cookie") or None
        if use_cookie:
            response = jsonify({"role": user.role.name.lower()})
            response.set_cookie(
                "token", token, secure=True, httponly=True, samesite="Strict"
            )
            return response
        else:
            return {"token": token, "role": user.role}
