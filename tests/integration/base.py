import hmac
import os
import requests

from flask import Flask, request, jsonify

WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
API_KEY = os.environ.get('API_KEY')

application = Flask(__name__)

with open('tests/integration/test.json') as test:
    contents = test.read().rstrip()
    print(contents)

digest = hmac.new(API_KEY.encode('utf-8'), contents.encode('utf-8'), digestmod="sha256").hexdigest()
print(digest)


@application.route("/", methods=['POST'])
def test_receiver():
    body = request.get_json()
    print(body)
    return jsonify("OK"), 200


@application.route("/test", methods=['POST'])
def test_scanner():
    session = requests.Session()
    headers = {
        'Content-Type': "application/json",
        'X-POLYSWARM-SIGNATURE': digest,
        'X-POLYSWARM-EVENT': 'bounty'
    }
    with session.post(WEBHOOK_URL, headers=headers, data=contents) as response:
        response.raise_for_status()
    return jsonify("OK"), 200

