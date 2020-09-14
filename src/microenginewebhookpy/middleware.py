import hmac
import os

API_KEY = os.environ.get('API_KEY')


class ValidateSenderMiddleware:
   def __init__(self, app):
       self.app = app

   def __call__(self, environ, start_response):
       wsgi_input = environ['wsgi.input'].read()
       signature = environ['HTTP_X_POLYSWARM_SIGNATURE'].read()
       if self.__valid_signature(wsgi_input, signature, API_KEY):
           return self.app(environ, start_response)
       else:
           return start_response("401 Not Authorized", [])

   @staticmethod
   def __valid_signature(body, signature, api_key):
       digest = hmac.new(api_key.encode('utf-8'), body).hexdigest()
       return hmac.compare_digest(digest, signature)
