from flask import Flask

from microenginewebhookspy.middleware import ValidateSenderMiddleware
from microenginewebhookspy.api import api

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/')
application = ValidateSenderMiddleware(app)
