import dataclasses
import datetime
import logging
import pytest

import microenginewebhookspy.tasks

from microenginewebhookspy.views import Bounty
from microenginewebhookspy.wsgi import app

from tests import EICAR_STRING


@pytest.fixture(autouse=True)
def replace_scan(celery_app):
    @celery_app.task
    def scan(bounty: Bounty):
        pass

    microenginewebhookspy.tasks.handle_bounty = scan


def test_valid_bounty_to_api(requests_mock):
    client = app.test_client()

    artifact_uri = 'mock://example.com/eicar'
    response_url = 'mock://example.com/response'
    eicar_sha356 = '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'
    # Setup http mocks
    requests_mock.get(artifact_uri, body=EICAR_STRING)
    requests_mock.post(response_url, text='Success')
    bounty = Bounty(id=987654321,
                    artifact_type='FILE',
                    artifact_uri=artifact_uri,
                    sha256=eicar_sha356,
                    mimetype='text/plain',
                    expiration=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    phase='assertion_window',
                    response_url=response_url,
                    rules={}
                    )
    headers = {'X-POLYSWARM-EVENT': 'bounty'}
    response = client.post('/', headers=headers, json=dataclasses.asdict(bounty))

    assert response.status_code == 202


def test_invalid_bounty_to_api():
    client = app.test_client()

    # Silencing expected log about the failure to parse this data
    logging.disable(logging.CRITICAL)
    headers = {'X-POLYSWARM-EVENT': 'bounty'}
    response = client.post('/', headers=headers, data={'asdf': 'fdsa'})
    logging.disable(logging.NOTSET)

    assert response.status_code == 400
