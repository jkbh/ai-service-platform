import os
import tempfile
from PIL import Image
from io import BytesIO
from werkzeug.security import generate_password_hash

import pytest

from ai_service_platform import create_app
from ai_service_platform.models import db, models
from ai_service_platform.models.models import Role, RequestStatus

ADMIN_ID = "7cb6e818-45f0-482e-90af-e35d2f56fbfd"
USER1_ID = "c8572b62-c5f4-419d-8744-dbee83c1ee58"
USER2_ID = "3fd89024-650a-49da-b12a-b930cfcf070c"
SOURCE_ID = "8b67fd71-cdbe-49ed-88b0-387970e8c3d0"
CLASSIFIER_ID = "9c707280-6603-4480-90e6-118a147794bc"
MOBILENET_ID = "9fb84eea-e685-4539-98c4-d76e8d939b88"
USER1_REQ_ID = "fad72c9c-4f20-468e-b2b9-b962800c14bc"
SOURCE_REQ_ID = "1f4b0a1c-8e9f-45f3-bf5f-04ce07bf2b6f"

IMAGE = Image.open("./tests/car.jpg")
with BytesIO() as output:
    IMAGE.save(output, format=IMAGE.format)
    BYTE_IMAGE = output.getvalue()


def fill_db():
    # admin role
    admin = models.User(
        public_id=ADMIN_ID,
        name="admin",
        password=generate_password_hash("admin"),
        role=Role.ADMIN,
    )
    db.session.add(admin)

    # user1 role
    user1 = models.User(
        public_id=USER1_ID,
        name="user1",
        password=generate_password_hash("user1"),
        role=Role.USER1,
    )
    db.session.add(user1)

    # user2 role
    user2 = models.User(
        public_id=USER2_ID,
        name="user2",
        password=generate_password_hash("user2"),
        role=Role.USER2,
    )
    db.session.add(user2)

    # source
    source = models.Source(
        public_id=SOURCE_ID,
        owner_id=USER2_ID,
        name="device1",
        password=generate_password_hash("source"),
        role=Role.SOURCE,
        owner=user2,
    )
    db.session.add(source)

    # ImageClassifier
    with open("./tests/ImageClassifier.h5", "rb") as f:
        model_h5 = models.Model(
            public_id=CLASSIFIER_ID,
            name=f.name,
            binary=f.read(),
            config={"shape": (32, 32), "expand_dims": True},
            type=".hdf5",
        )
        db.session.add(model_h5)

    # MobileNetClassifier Built-in
    model_mobile = models.Model(
        public_id=MOBILENET_ID,
        name="MobileNet",
        config={"shape": (224, 224), "expand_dims": True},
    )
    db.session.add(model_mobile)

    # request from user1
    request_user1 = models.Request(
        public_id=USER1_REQ_ID,
        user_id=USER1_ID,
        model_id=CLASSIFIER_ID,
        input=BYTE_IMAGE,
        output="[test_output]",
        status=RequestStatus.FINISHED,
        user=user1,
        model=model_h5,
    )
    db.session.add(request_user1)

    # request from source
    request_source = models.Request(
        public_id=SOURCE_REQ_ID,
        user_id=USER2_ID,
        source_id=SOURCE_ID,
        model_id=CLASSIFIER_ID,
        input=BYTE_IMAGE,
        output="[test_output]",
        status=RequestStatus.FINISHED,
        user=user2,
        source=source,
        model=model_mobile,
    )
    db.session.add(request_source)

    db.session.commit()


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""

    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_path}
    )

    with app.app_context():
        fill_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def flask_test_client(app):
    return app.test_client()


class TestClient(object):
    def __init__(self, client):
        self._client = client
        self._token = None

    def login(self, name, password, source=False, use_cookie=False):
        response = self._client.post(
            "auth/login",
            json={
                "name": name,
                "password": password,
                "source": source,
                "use_cookie": use_cookie,
            },
        )
        if response.status_code == 200:
            self._token = response.get_json()["token"]
        return response

    def get(self, uri):
        response = self._client.get(uri, headers={"x-access-token": self._token})
        return response

    def post(self, uri, json):
        response = self._client.post(
            uri, headers={"x-access-token": self._token}, json=json
        )
        return response

    def delete(self, uri):
        response = self._client.delete(uri, headers={"x-access-token": self._token})
        return response


@pytest.fixture
def client(flask_test_client):
    return TestClient(flask_test_client)
