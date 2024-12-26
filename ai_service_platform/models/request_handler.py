from flask import current_app
import numpy as np
import os

os.environ["KERAS_BACKEND"] = "jax"
import keras
from PIL import Image
from tempfile import NamedTemporaryFile

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

    model = request.model

    input_image = Image.open(
        os.path.join(current_app.config["UPLOAD_FOLDER"], request.input_file),
    ).convert(
        "RGB"
    )  # PNGs can open as RGB or RGBA, we always want RGB (3 channels expected by classifier)

    try:
        input_image = input_image.resize(model.config["shape"])  # type: ignore
    except KeyError:
        print("No input shape configuration found in database. Did not resize input.")

    input_image = np.expand_dims(input_image, axis=0)  # type: ignore

    if model.binary:
        loaded_model = load_model_from_binary(
            bytes(str(model.binary), encoding="st"), model.type
        )

        input_array = np.array(input_image)
        predictions = loaded_model.predict(input_array)
    else:
        loaded_model = keras.applications.MobileNet()

        input_array = keras.applications.mobilenet.preprocess_input(input_image)
        predictions = loaded_model.predict(input_array)
        predictions = keras.applications.mobilenet.decode_predictions(predictions)

    request.status = RequestStatus.FINISHED
    request.output = predictions[0]
    db.session.commit()


def load_model_from_binary(bytes: bytes, type: str) -> keras.Model:
    """Loads the AI model from the database into a keras.Model object

    Args:
        model: the model to load

    Returns:
        model: The loaded keras model
    """
    with NamedTemporaryFile(dir="./tests/", suffix=type, delete=False) as fd:
        fd.write(bytes)

    with open(fd.name, "rb") as fd:
        model = keras.models.load_model(fd.name)

    os.remove(fd.name)

    return model  # type: ignore
