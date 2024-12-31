import os
from flask import (
    Flask,
    render_template,
    flash,
    redirect,
    url_for,
    g,
    send_from_directory,
)

from ai_service_platform.models.models import Base

from .models import db

from .views.request import bp as request_bp
from .views.auth import bp as auth_bp
from .views.source import bp as source_bp
from .views.model import bp as model_bp
from .views.user import bp as user_bp


def create_app(test_config=None) -> Flask:
    """Creates the flask app object"""

    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "dev"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "flask-test.db"
    )
    app.config["SQLALCHEMY_ENGINES"] = {
        "default": "sqlite:///" + os.path.join(app.instance_path, "flask-test.db")
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Create instance folders if they do not exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # These warnings pop up when Schemas get instantiated with certain keywords like 'exclude' or 'only'.
    # Because these warnings are just a reminder that the modified Schemas are automatically renamed on runtime,
    # they can by ignored.
    # warnings.filterwarnings("ignore", message="Multiple schemas resolved to the name ")

    @app.route("/index")
    @app.route("/")
    def index():
        if g.user is None:
            flash("Log in please")
            return redirect(url_for("auth.login"))
        return render_template("index.html")

    @app.route("/uploads/<path:name>")
    def send_uploaded_file(name):
        return send_from_directory(app.config["UPLOAD_FOLDER"], name)

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(request_bp)
    app.register_blueprint(source_bp)
    app.register_blueprint(model_bp)

    # init flask-sqlalchemy orm
    # db.init_app(app)
    app.config.from_prefixed_env()
    db.init_app(app)

    with app.app_context():
        Base.metadata.create_all(db.engine)

    # init flask-marshmallow object serializer/deserializer
    # ma.init_app(app)

    return app
