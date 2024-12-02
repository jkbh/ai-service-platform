FROM python:3.9-slim-buster

WORKDIR /ai-service-platform

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=backend
ENV FLASK_ENV=production
CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]