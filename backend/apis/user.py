import uuid

from werkzeug.security import generate_password_hash

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import pre_load, post_load
from marshmallow_enum import EnumField

from . import ma
from backend.core import db
from backend.core import models
from backend.core.models import Role
from .auth import roles_required


bp = Blueprint('user', __name__, url_prefix='/user')


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serialization and deserialization of user objects"""
    class Meta:
        model = models.User

    role = EnumField(Role)

    @pre_load
    def create_uuid(self, data, **kwargs):
        if 'public_id' not in data:
            data['public_id'] = str(uuid.uuid4())
        # Previously the request had lowercase roles, ensure uppercase for backwards compatibility
        if 'role' in data:
            data['role'] = str(data['role']).upper()
        return data

    @post_load
    def hash_password(self, data, **kwargs):
        data['password'] = generate_password_hash(
            data['password'],  method='sha256')
        return data


@bp.route('')
class UserList(MethodView):
    @bp.response(200, UserSchema(many=True, only=('public_id', 'name', 'role',)))
    @roles_required([Role.ADMIN])
    def get(self):
        users = models.User.query.all()
        return users

    @roles_required([Role.ADMIN])
    @bp.arguments(UserSchema)
    @bp.response(201, UserSchema(only=('public_id', 'name', 'role',)))
    def post(self, data):
        user = models.User(**data)
        db.session.add(user)
        db.session.commit()

        return user


@bp.route('/<public_id>')
class User(MethodView):
    @bp.response(200, UserSchema)
    @roles_required([Role.ADMIN])
    def get(self, public_id):
        user = db.session.get(models.User, public_id)
        if not user:
            abort(404, message='Could not find user')
        return user

    @bp.response(200, UserSchema)
    @roles_required([Role.ADMIN])
    def delete(self, public_id):
        user = db.session.get(models.User, public_id)

        if not user:
            abort(404, message='Could not find user')

        db.session.delete(user)
        db.session.commit()

        return user
