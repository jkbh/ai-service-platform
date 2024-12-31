import os
from threading import Thread
import uuid

from flask import (
    Blueprint,
    abort,
    copy_current_request_context,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select
from werkzeug.utils import secure_filename

from ai_service_platform.models import db, models
from ai_service_platform.models.models import Model, Role, Request
from ai_service_platform.models.request_handler import process_request

from .auth import roles_required

ALLOWED_EXTENSIONS = {"png", "jpeg", "jpg"}


def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


bp = Blueprint("request", __name__, url_prefix="/request")


@bp.route("")
@roles_required([Role.ADMIN, Role.USER1, Role.USER2])
def get():
    requests = None
    if g.user.role == Role.ADMIN:
        requests = db.session.scalars(select(Request)).all()
    else:
        requests = g.user.requests

    models = db.session.scalars(select(Model)).all()
    return render_template("request/list.html", requests=requests, models=models)


@bp.route("", methods=["POST"])
@roles_required([Role.USER1, Role.SOURCE])
def users_post():
    # Securely handle the input file upload and storage
    if "input" not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files["input"]
    if file.filename is None:
        flash("File has no name")
        return redirect(request.url)

    filename = secure_filename(file.filename)

    if not is_allowed_file(filename):
        flash("Wrong filetype")
        return redirect(request.url)

    input_id = uuid.uuid4()
    filename = f"{input_id}_{filename}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

    # Set user and/or source of http request
    source = None
    if g.user.role is Role.SOURCE:
        user = g.user.owner
        source = g.user
    else:
        user = g.user

    # Prepare request db object columns
    data = {
        "model_id": uuid.UUID(request.form["model"]),
        "user_id": g.user.public_id,
        # "input_name": filename,
        "input_file": filename,
    }

    model = db.session.get(models.Model, data["model_id"])

    newRequest = models.Request(**data, user=user, source=source, model=model)
    db.session.add(newRequest)
    db.session.commit()

    @copy_current_request_context
    def process(public_id):
        """Wrapper to process requests in parallel while staying in the same request context"""
        process_request(public_id)

    thread = Thread(target=process, kwargs={"public_id": newRequest.public_id})
    thread.start()

    return redirect(url_for("request.get"))


@bp.route("/<uuid:public_id>")
@roles_required([Role.USER1, Role.USER2])
def get_request(public_id):
    request = db.session.scalar(
        select(Request).filter_by(public_id=public_id, user_id=g.user.public_id)
    )

    if not request:
        abort(404, message="Could not find request")

    return render_template("request/item.html", request=request)


@bp.route("/<uuid:public_id>/table-status")
@roles_required([Role.USER1, Role.USER2])
def get_table_status(public_id):
    request = db.session.scalar(
        select(Request).filter_by(public_id=public_id, user_id=g.user.public_id)
    )

    if not request:
        abort(404, message="Could not find request")

    return render_template("request/table_status.html", request=request)


@bp.route("/<uuid:public_id>", methods=["DELETE"])
@roles_required([Role.USER1, Role.USER2])
def delete(public_id):
    request = db.session.scalar(
        select(Request).filter_by(public_id=public_id, user_id=g.user.public_id)
    )

    if not request:
        abort(404, message="Could not find request")

    db.session.delete(request)
    db.session.commit()

    return ""
