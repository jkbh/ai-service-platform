from flask import (
    request,
    g,
    render_template,
    session,
    redirect,
    url_for,
    flash,
    Blueprint,
)

from sqlalchemy import select
from werkzeug.security import check_password_hash
from functools import wraps

from ai_service_platform.core.models import User, Role
from ai_service_platform.core import db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def roles_required(allowed: list[Role]):
    """Checks if current user has at least one of the allowed roles

    This decorator used the g object to read the current user.

    Args:
    allowed: A list of allowed roles. Can be any combination of user1, user2, admin, dev, source
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user is None:
                flash("Not logged in")
                return redirect(url_for("auth.login", next_page=request.url))
            if g.user.role not in allowed:
                flash("Access denied")
                return redirect(request.referrer)

            return f(*args, **kwargs)

        return decorated

    return decorator


@bp.before_app_request
def load_logged_in_user():
    """Load user from the current session cookie"""
    g.user = None
    user_id: str | None = session.get("user_id")

    if user_id:
        try:
            g.user = db.session.get_one(User, user_id)
        except Exception:
            pass


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.session.scalar(select(User).filter_by(name=username))

        if not user or not check_password_hash(user.password, password):
            flash("Incorrect username or password")
            return redirect(request.url)

        session.clear()
        session["user_id"] = user.public_id

        next_page = request.args.get("next_page")
        if next_page:
            return redirect(next_page)

        return redirect(url_for("index"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
