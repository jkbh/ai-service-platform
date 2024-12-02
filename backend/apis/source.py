from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import pre_load, post_load
from marshmallow_enum import EnumField
import uuid

from werkzeug.security import generate_password_hash

from . import ma
from backend.core import db
from backend.core import models
from backend.core.models import Role
from .auth import roles_required

bp = Blueprint("source", __name__, url_prefix="/source")


class SourceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.Source
        include_fk = True

    role = EnumField(Role)

    @pre_load
    def fill_missing_data(self, data, **kwargs):
        if "public_id" not in data:
            data["public_id"] = str(uuid.uuid4())
        if "owner_id" not in data:
            data["owner_id"] = g.user.public_id
        data["role"] = "SOURCE"
        return data

    @post_load
    def hash_password(self, data, **kwargs):
        data["password"] = generate_password_hash(data["password"])
        return data


@bp.route("")
class SourceList(MethodView):
    @roles_required([Role.USER2])
    @bp.response(200, SourceSchema(many=True))
    def get(self):
        user_sources = g.user.sources

        return user_sources

    @roles_required([Role.USER2])
    @bp.arguments(SourceSchema)
    @bp.response(201, SourceSchema)
    def post(self, data):
        source = models.Source(**data, owner=g.user)
        db.session.add(source)
        db.session.commit()

        return source


@bp.route("/<public_id>")
class Source(MethodView):
    @roles_required([Role.ADMIN, Role.USER2])
    @bp.response(200, SourceSchema)
    def delete(self, public_id):
        source = db.session.get(models.Source, public_id)

        if not source:
            abort(404, "Could not delete source")

        db.session.delete(source)
        db.session.commit()

        return source
