from flask import render_template, Blueprint
from sqlalchemy import select

from .auth import roles_required
from ai_service_platform.models.models import Role, Model
from ai_service_platform.models import db

bp = Blueprint("model", __name__, url_prefix="/model")


@bp.route("")
@roles_required([Role.USER1, Role.SOURCE])
def model():
    models = db.session.scalars(select(Model))

    return render_template("models.html", models=models)
