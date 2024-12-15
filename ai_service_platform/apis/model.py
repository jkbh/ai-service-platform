from flask.views import MethodView
from flask_smorest import Blueprint

from . import ma
from .auth import roles_required
from ai_service_platform.core import models
from ai_service_platform.core.models import Role

bp = Blueprint('model', __name__, url_prefix='/model')


class ModelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.Model


@bp.route('')
class ModelList(MethodView):
    @roles_required([Role.USER1, Role.SOURCE])
    @bp.response(200, ModelSchema(many=True))
    def get(self):
        all_models = models.Model.query.with_entities(models.Model.public_id, models.Model.name).all()

        return all_models
