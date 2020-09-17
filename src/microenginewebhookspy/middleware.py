import hmac
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
            start_response("400 Bad Request", [('Content-Length', '0')])
            return []

        if self.__valid_signature(wsgi_input, signature, API_KEY):
            environ['wsgi.input'] = BytesIO(wsgi_input)
            return self.app(environ, start_response)
        else:
            start_response("401 Not Authorized", [('Content-Length', '0')])
            return []

    @staticmethod
    def __valid_signature(body, signature, api_key):
        digest = hmac.new(api_key.encode('utf-8'), body, digestmod="sha256").hexdigest()
        logger.debug('Comparing computed %s vs given %s', digest, signature)
        return hmac.compare_digest(digest, signature)
