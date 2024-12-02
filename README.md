# ai-service-platform

REST-API Server based on flask

Main Dependencies:

- [flask](https://flask.palletsprojects.com/en/1.1.x/) as the base backend framework
- [flask-smorest](https://flask-smorest.readthedocs.io/en/latest/) for enhanced REST
  functionality and OpenAPI doc generation
- [flask-sqlalchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) as ORM
- [flask-marshmallow](https://flask-marshmallow.readthedocs.io/en/latest/) for serialization/deserialization

The easiest way to run the server is to build the provided dockerfile and running the image with a published port 5000.

## Python Setup

Download a supported Python Version (3.6, 3.7, 3.8, 3.9)

Navigate into backend folder

It is recommended to use a virtual environment package like [venv](https://docs.python.org/3/library/venv.html) to keep a local python installation. To install the required python packages run:

`pip install -r requirements.txt`

## Flask Setup

Configure the flask app environment variable:

`$env:FLASK_APP='backend'` (Windows)

`$export FLASK_APP='backend'` (Unix)

Now you can start the app with:

`flask run`

If no database instance is found, a new sqlite db gets created. There are default admin:admin und user1:user1 accounts.

## OpenAPI Docs

To view the REST API Swagger Documentation visit http://localhost:5000/swagger-ui when the server is running.
