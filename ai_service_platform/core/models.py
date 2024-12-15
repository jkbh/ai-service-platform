import uuid

from . import db
from sqlalchemy import event
from sqlalchemy.dialects.sqlite.json import JSON
from flask import current_app
from werkzeug.security import generate_password_hash
from enum import Enum, auto


class Role(Enum):
    """Role of a user in the system"""

    ADMIN = auto()
    DEV = auto()
    USER1 = auto()
    USER2 = auto()
    SOURCE = auto()


class RequestStatus(Enum):
    """The  status of a request"""

    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    FAILED = auto()
    FINISHED = auto()


class User(db.Model):
    public_id = db.Column(db.Text, primary_key=True, nullable=False, default=str(uuid.uuid4()))
    name = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    requests = db.relationship('Request', back_populates='user', cascade="all, delete")
    sources = db.relationship('Source', back_populates='owner', cascade="all, delete")


@event.listens_for(User.__table__, 'after_create')
def create_users(*args, **kwargs):
    if current_app.config['TESTING']:
        return
    db.session.add(
        User(public_id=str(uuid.uuid4()), name='admin', password=generate_password_hash('admin'), role=Role.ADMIN))
    db.session.add(
        User(public_id=str(uuid.uuid4()), name='user1', password=generate_password_hash('user1'), role=Role.USER1))
    db.session.commit()


class Request(db.Model):
    public_id = db.Column(db.Text, primary_key=True, default=str(uuid.uuid4()))
    user_id = db.Column(db.Text, db.ForeignKey('user.public_id', ondelete='CASCADE'), nullable=False)
    source_id = db.Column(db.Text, db.ForeignKey('source.public_id', ondelete='CASCADE'))
    model_id = db.Column(db.Text, db.ForeignKey('model.public_id', ondelete="CASCADE"), nullable=False)
    patient_id = db.Column(db.Text)
    input = db.Column(db.LargeBinary, nullable=False)
    output = db.Column(db.Text)
    status = db.Column(db.Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    user = db.relationship('User', back_populates='requests')
    source = db.relationship('Source', back_populates='requests')
    model = db.relationship('Model', back_populates='requests')


class Model(db.Model):
    public_id = db.Column(db.Text, primary_key=True, default=str(uuid.uuid4()))
    name = db.Column(db.Text, unique=True, nullable=False)
    binary = db.Column(db.LargeBinary)
    config = db.Column(JSON)
    type = db.Column(db.Text)
    requests = db.relationship(
        'Request', back_populates='model', cascade="all, delete")


@event.listens_for(Model.__table__, 'after_create')
def create_models(*args, **kwargs):
    if current_app.config['TESTING']:
        return
    db.session.add(
        Model(public_id='9fb84eea-e685-4539-98c4-d76e8d939b88', name='MobileNet',
              config={'shape': (224, 224), 'expand_dims': True}))
    db.session.commit()


class Source(db.Model):
    public_id = db.Column(db.Text, primary_key=True, default=str(uuid.uuid4()))
    owner_id = db.Column(db.Text, db.ForeignKey(
        'user.public_id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.SOURCE)
    owner = db.relationship(
        'User', back_populates='sources')
    requests = db.relationship(
        'Request', back_populates='source')
