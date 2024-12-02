import base64
from uuid import uuid4
from threading import Thread

from flask import g, copy_current_request_context
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import pre_load, fields, ValidationError, post_dump
from marshmallow_enum import EnumField

from . import ma
from backend.core import db
from backend.core import models
from backend.core.models import Role, RequestStatus
from backend.core.request_handler import process_request

from .auth import roles_required

bp = Blueprint('request', __name__, url_prefix='/request')


class BytesField(fields.Field):
    """Custom marshmallow field with base64 encoding support"""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return base64.b64encode(value).decode('utf-8')

    def _deserialize(self, value, attr, obj, **kwargs):
        try:
            return base64.b64decode(value)
        except ValueError as error:
            raise ValidationError('Could not deserialize base64 string') from error


class RequestSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.Request
        include_fk = True

    input = BytesField(required=True)
    status = EnumField(RequestStatus)

    @pre_load
    def create_uuid(self, data, **kwargs):
        if 'public_id' not in data:
            data['public_id'] = str(uuid4())
        return data

    @pre_load
    def set_status(self, data, **kwargs):
        if 'status' not in data:
            data['status'] = RequestStatus.PENDING.name
        return data

    @pre_load
    def set_user_source(self, data, **kwargs):
        if g.user.role == Role.SOURCE:
            # Set user to the owner of the source that sent the request,
            data['user_id'] = g.user.owner_id
            data['source_id'] = g.user.public_id
        else:
            # Set user to request sender
            data['user_id'] = g.user.public_id
        return data

    @post_dump
    def status_to_lowercase(self, data, **kwargs):
        if 'status' in data:
            data['status'] = data['status'].lower()  # temporary workaround for client compatibility
        return data


@bp.route('')
class RequestList(MethodView):
    @roles_required([Role.ADMIN, Role.USER1, Role.USER2])
    @bp.response(200, RequestSchema(many=True))
    def get(self):
        if g.user.role == Role.ADMIN:
            return models.Request.query.all()
        return g.user.requests

    @roles_required([Role.USER1, Role.SOURCE])
    @bp.arguments(RequestSchema)
    @bp.response(201, RequestSchema)
    def post(self, data):
        source = None
        if g.user.role is Role.SOURCE:
            user = g.user.owner
            source = g.user
        else:
            user = g.user

        model = db.session.get(models.Model, data['model_id'])

        if not model:
            abort(404, 'Model not found')

        request = models.Request(**data, user=user, source=source, model=model)
        request_id = request.public_id
        db.session.add(request)
        db.session.commit()

        @copy_current_request_context
        def process(public_id):
            """Wrapper to process requests in parallel while staying in the same request context"""
            process_request(public_id)

        thread = Thread(target=process, kwargs={'public_id': request_id})
        thread.start()

        return request


@bp.route('/<public_id>')
class Request(MethodView):
    @roles_required([Role.USER1, Role.USER2])
    @bp.response(200, RequestSchema)
    def get(self, public_id):
        request = db.session.get(models.Request, public_id)

        if not request:
            abort(404, message='Could not find request')

        if request not in g.user.requests:
            abort(403, message='Not allowed')

        return request

    @bp.response(200, RequestSchema)
    @roles_required([Role.USER1, Role.USER2])
    def delete(self, public_id):
        request = db.session.get(models.Request, public_id)

        if not request:
            abort(404, message='Could not find request')

        if request not in g.user.requests:
            abort(403, message='Could not delete request')

        db.session.delete(request)
        db.session.commit()

        return request
