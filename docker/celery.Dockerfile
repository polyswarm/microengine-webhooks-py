FROM python:3.7-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN pip install .

CMD celery -A microenginewebhookspy.scan worker
