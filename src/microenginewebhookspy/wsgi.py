from flask import Flask
from logging.config import dictConfig
from microenginewebhookspy import settings

from microenginewebhookspy.middleware import ValidateSenderMiddleware
from microenginewebhookspy.views import api

dictConfig(settings.LOGGING)

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/')
application = ValidateSenderMiddleware(app)
