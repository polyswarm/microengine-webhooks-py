import hashlib
import hmac
import json
import logging
from io import BytesIO

from microenginewebhookspy.settings import WEBHOOK_SECRET

logger = logging.getLogger(__name__)


REQUEST_METHOD_WHITELIST = ['GET']


class ValidateSenderMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] in REQUEST_METHOD_WHITELIST:
            return self.app(environ, start_response)

        wsgi_input = environ['wsgi.input'].read()
        try:
            # added .encode().decode() to make this work in python 3.8+
            signature = environ['HTTP_X_POLYSWARM_SIGNATURE'].encode('utf-8')
            logger.debug('Type signature: %r', type(signature).__name__)
        except KeyError:
            message = json.dumps({"X-POLYSWARM-SIGNATURE": "Signature not included in headers"}).encode('utf-8')
            start_response("400 Bad Request",
                           [('Content-Length', f'{len(message)}'), ('Content-Type', 'application/json')])
            return [message]

        if self._valid_signature(wsgi_input, signature, WEBHOOK_SECRET):
            environ['wsgi.input'] = BytesIO(wsgi_input)
            return self.app(environ, start_response)
        else:
            message = json.dumps({"X-POLYSWARM-SIGNATURE": "Signature does not match body"}).encode('utf-8')
            start_response("401 Not Authorized",
                           [('Content-Length', f'{len(message)}'), ('Content-Type', 'application/json')])
            return [message]

    @staticmethod
    def _valid_signature(body, signature, secret):
        digest = hmac.new(secret.encode('utf-8'), body, digestmod=hashlib.sha256).digest()
        logger.debug(b'Comparing computed digest "%r" (%d) vs given signature "%r" (%d)', digest, len(digest), signature, len(signature))
        # assert _is_ascii(digest)
        # assert _is_ascii(signature)
        return hmac.compare_digest(digest, signature)


def _is_ascii(digest):
    try:
        digest.encode('ascii')
    except UnicodeEncodeError:
        logger.debug('Digest %s is not ascii', digest)
        return False
    else:
        return True

