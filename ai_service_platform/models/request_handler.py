from flask import current_app
import os
import requests

from . import db
from .models import Request, RequestStatus


def process_request(request_id: str) -> None:
    """Handles the predictions of an ai request. The request is loaded from the database an then the model is run

    Args:
        request_id: The public_id of the request to process

    Returns:
        A list of predictions
    """
    request = db.session.get(Request, request_id)
    if not request:
        return

    request.status = RequestStatus.RUNNING
    db.session.commit()

    input_path = os.path.join(current_app.config["UPLOAD_FOLDER"], request.input_file)
    prediction_url = f"http://multi-model-server:8080/predictions/{request.model.server_model_name}"

    with open(input_path, "rb") as file:
        response = requests.post(prediction_url, data=file).json()

    request.status = RequestStatus.FINISHED
    request.output = response
    db.session.commit()
