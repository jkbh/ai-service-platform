import os
import warnings
from flask import Flask

from .core import db
from .apis import api
from .apis import ma

from .apis.request import bp as request_bp
from .apis.auth import bp as auth_bp
from .apis.source import bp as source_bp
from .apis.model import bp as model_bp
from .apis.user import bp as user_bp


def create_app(test_config=None) -> Flask:
    """Creates the flask app object"""

    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = "dev"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "flask-test.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["API_TITLE"] = "ai-service-platform"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["OPENAPI_URL_PREFIX"] = ""
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # init flask-smorest api
    api.init_app(app)

    # These warnings pop up when Schemas get instantiated with certain keywords like 'exclude' or 'only'.
    # Because these warnings are just a reminder that the modified Schemas are automatically renamed on runtime,
    # they can by ignored.
    warnings.filterwarnings("ignore", message="Multiple schemas resolved to the name ")

    api.register_blueprint(auth_bp)
    api.register_blueprint(user_bp)
    api.register_blueprint(request_bp)
    api.register_blueprint(source_bp)
    api.register_blueprint(model_bp)

    # init flask-sqlalchemy orm
    db.init_app(app)
    with app.app_context():
        db.create_all()
    # init flask-marshmallow object serializer/deserializer
    ma.init_app(app)

    return app
