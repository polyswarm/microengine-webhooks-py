import hmac
import json
import logging
from io import BytesIO

from microenginewebhookspy.settings import API_KEY

logger = logging.getLogger(__name__)


class ValidateSenderMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        wsgi_input = environ['wsgi.input'].read()
        try:
            signature = environ['HTTP_X_POLYSWARM_SIGNATURE']
        except KeyError:
            message = json.dumps({"X-POLYSWARM-SIGNATURE": "Signature not included in headers"}).encode('utf-8')
            start_response("400 Bad Request",
                           [('Content-Length', f'{len(message)}'), ('Content-Type', 'application/json')])
            return [message]

        if self._valid_signature(wsgi_input, signature, API_KEY):
            environ['wsgi.input'] = BytesIO(wsgi_input)
            return self.app(environ, start_response)
        else:
            message = json.dumps({"X-POLYSWARM-SIGNATURE": "Signature does not match body"}).encode('utf-8')
            start_response("401 Not Authorized",
                           [('Content-Length', f'{len(message)}'), ('Content-Type', 'application/json')])
            return [message]

    @staticmethod
    def _valid_signature(body, signature, api_key):
        digest = hmac.new(api_key.encode('utf-8'), body, digestmod="sha256").hexdigest()
        logger.debug('Comparing computed %s vs given %s', digest, signature)
        return hmac.compare_digest(digest, signature)
