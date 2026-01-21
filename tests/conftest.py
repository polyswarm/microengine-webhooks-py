import pytest
from werkzeug.test import Client

from microenginewebhookspy.wsgi import application, ValidateSenderMiddleware


@pytest.fixture
def wsgi_app():
    from polyswarm_engine.wsgi import backend
    from microenginewebhookspy.engine import engine

    # Wire the WSGI to the Engine directly
    # so no Celery queue will be needed during the server tests.
    backend._analyze = engine._analyze
    backend._head = engine._head
    backend.app.conf.task_always_eager = True

    # Ensure Celery is setup properly
    with backend.run():
        # ValidateSenderMiddlew becomes a noop with no `secret` param
        # but we at least know that it is not breaking stuff.
        wsgi = ValidateSenderMiddleware(application)
        yield Client(wsgi)
