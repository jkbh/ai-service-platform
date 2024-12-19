from flask import abort, g, Blueprint
from flask.views import MethodView

from ai_service_platform.core import db
from ai_service_platform.core import models
from ai_service_platform.core.models import Role
from .auth import roles_required

bp = Blueprint("source", __name__, url_prefix="/source")


class SourceList(MethodView):
    @bp.route("")
    @roles_required([Role.USER2])
    # @bp.response(200, SourceSchema(many=True))
    def get(self):
        user_sources = g.user.sources

        return user_sources

    @bp.route("")
    @roles_required([Role.USER2])
    def post(self, data):
        source = models.Source(**data, owner=g.user)
        db.session.add(source)
        db.session.commit()

        return ""


class Source(MethodView):
    @roles_required([Role.ADMIN, Role.USER2])
    @bp.route("/<public_id>")
    def delete(self, public_id):
        source = db.session.get(models.Source, public_id)

        if not source:
            abort(404, "Could not delete source")

        db.session.delete(source)
        db.session.commit()

        return ""
