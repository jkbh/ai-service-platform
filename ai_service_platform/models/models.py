from typing import Optional, Any
from typing_extensions import Annotated
import uuid
from sqlalchemy.orm.properties import MappedColumn

from . import db
from sqlalchemy import PickleType, event, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship, DeclarativeBase
from sqlalchemy.dialects.sqlite import JSON
from flask import current_app
from werkzeug.security import generate_password_hash
import enum


class Role(enum.Enum):
    """Role of a user in the system"""

    ADMIN = "admin"
    DEV = "dev"
    USER1 = "user1"
    USER2 = "user2"
    SOURCE = "source"


class RequestStatus(enum.Enum):
    """The  status of a request"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    FINISHED = "finished"


bytes_pickle = Annotated[Any, "pickle"]


class Base(DeclarativeBase):
    type_annotation_map = {
        dict[str, Any]: JSON,
        bytes_pickle: PickleType,
    }


class User(Base):
    __tablename__ = "user"
    public_id: MappedColumn[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    role: Mapped[Role]
    requests: Mapped[list["Request"]] = relationship(
        back_populates="user", cascade="all, delete"
    )
    sources: Mapped[list["Source"]] = relationship(
        back_populates="owner", cascade="all, delete"
    )


@event.listens_for(User.__table__, "after_create")
def create_users(*args, **kwargs):
    if current_app.config["TESTING"]:
        return
    db.session.add(
        User(
            public_id=uuid.uuid4(),
            name="admin",
            password=generate_password_hash("admin"),
            role=Role.ADMIN,
        )
    )
    db.session.add(
        User(
            public_id=uuid.uuid4(),
            name="user1",
            password=generate_password_hash("user1"),
            role=Role.USER1,
        )
    )
    db.session.commit()


class Request(Base):
    __tablename__ = "request"
    public_id: MappedColumn[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.public_id", ondelete="CASCADE")
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("source.public_id", ondelete="CASCADE")
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model.public_id", ondelete="CASCADE")
    )
    patient_id: Mapped[Optional[str]]
    # input_name: Mapped[str]
    input_file: Mapped[str]
    output: Mapped[Optional[bytes_pickle]]
    status: Mapped[RequestStatus] = mapped_column(default=RequestStatus.PENDING)
    user: Mapped[User] = relationship(back_populates="requests")
    source: Mapped["Source"] = relationship(back_populates="requests")
    model: Mapped["Model"] = relationship(back_populates="requests")


class Model(Base):
    __tablename__ = "model"
    public_id: MappedColumn[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(unique=True)
    binary: Mapped[Optional[bytes]]
    config: Mapped[dict[str, Any]]
    type: Mapped[str]
    requests: Mapped[list[Request]] = relationship(
        back_populates="model", cascade="all, delete"
    )


@event.listens_for(Model.__table__, "after_create")
def create_models(*args, **kwargs):
    if current_app.config["TESTING"]:
        return
    db.session.add(
        Model(
            public_id=uuid.uuid4(),
            name="MobileNet",
            config={"shape": (224, 224), "expand_dims": True},
            type="keras",
        )
    )
    db.session.commit()


class Source(Base):
    __tablename__ = "source"
    public_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.public_id"))
    name: Mapped[str]
    password: Mapped[str]
    role: Mapped[Role] = mapped_column(default=Role.SOURCE)
    owner: Mapped[list[User]] = relationship(back_populates="sources")
    requests: Mapped[list[Request]] = relationship(back_populates="source")
