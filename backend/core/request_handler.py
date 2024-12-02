import numpy as np
import os
import keras.models
from keras.applications.mobilenet import MobileNet, preprocess_input, decode_predictions
from io import BytesIO
from PIL import Image
from tempfile import NamedTemporaryFile

from . import db
from .models import Request, Model, RequestStatus


def process_request(request_id: str) -> None:
    """Handles the predictions of an ai request. The request is loaded from the database an then the model is run

    Args:
        request_id: The public_id of the request to process

    Returns:
        A list of predictions
    """
    request = Request.query.filter_by(public_id=request_id).first()
    request.status = RequestStatus.RUNNING
    db.session.commit()

    model = request.model

    input_image = Image.open(BytesIO(request.input))

    try:
        input_image = input_image.resize(model.config['shape'])
    except KeyError:
        print("No input shape configuration found in database. Did not resize input.")

    input_image = np.expand_dims(input_image, axis=0)

    if model.binary:
        loaded_model = load_model_from_binary(model)

        input_array = np.array(input_image)
        predictions = loaded_model.predict(input_array)
    else:
        loaded_model = MobileNet()

        input_array = preprocess_input(input_image)
        predictions = loaded_model.predict(input_array)
        predictions = decode_predictions(predictions)

    request.status = RequestStatus.FINISHED
    request.output = str(predictions)
    db.session.commit()


def load_model_from_binary(model: Model) -> keras.Model:
    """Loads the AI model from the database into a keras.Model object

    Args:
        model: the model to load

    Returns:
        model: The loaded keras model
    """

    with NamedTemporaryFile(dir='./tests/', suffix=model.type, delete=False) as fd:
        fd.write(model.binary)

    with open(fd.name, 'rb') as fd:
        model = keras.models.load_model(fd.name)

    os.remove(fd.name)

    return model
