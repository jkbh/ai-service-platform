import uuid

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
)

from ai_service_platform.models import db
from ai_service_platform.models import models
from ai_service_platform.models.models import Role, User
from .auth import roles_required


bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("", methods=["GET", "POST"])
@roles_required([Role.ADMIN])
def user():
    if request.method == "POST":
        data = {
            "name": request.form["username"],
            "password": generate_password_hash(request.form["password"]),
            "role": request.form["role"],
        }

        user = models.User(**data)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.close()
            flash("Error creating user")

    users = db.session.scalars(select(User))
    return render_template(
        "users.html",
        users=users,
        roles=[Role.ADMIN, Role.USER1, Role.USER2, Role.DEV],
    )


@bp.route("/<uuid:public_id>", methods=["DELETE"])
@roles_required([Role.ADMIN])
def delete(public_id):
    user = db.session.get(models.User, public_id)

    if not user:
        return "", 404

    db.session.delete(user)
    db.session.commit()

    return ""
