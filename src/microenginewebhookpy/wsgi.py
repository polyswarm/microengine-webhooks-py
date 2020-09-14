import dataclasses

from typing import List
from flask import Flask, request, jsonify

from microenginewebhookpy.middleware import ValidateSenderMiddleware
from microenginewebhookpy import scan

app = Flask(__name__)


@dataclasses.dataclass
class Bounty:
    guid: str
    artifact_type: str
    artifact_url: str
    sha256: str
    mimetype: str
    expiration: str
    phase: str
    response_url: str
    rules: List[str]


@app.route('/', method='POST')
def bounty_handler():
    event_name = request.json["name"]

    if event_name == 'bounty':
        bounty = Bounty(**request.json["data"])
        scan.delay(bounty)

    return jsonify('OK'), 200


application = ValidateSenderMiddleware(app)
