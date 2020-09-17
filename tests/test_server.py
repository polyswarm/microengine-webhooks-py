import dataclasses
import datetime
import pytest

import microenginewebhookspy.scan

from microenginewebhookspy.api import Bounty
from microenginewebhookspy.scan import EICAR_STRING
from microenginewebhookspy.wsgi import app


@pytest.fixture(autouse=True)
def replace_scan(celery_app):
    @celery_app.task
    def scan(bounty: Bounty):
        pass

    microenginewebhookspy.scan.scan = scan


def test_valid_bounty_to_api(requests_mock):
    client = app.test_client()

    artifact_url = 'mock://example.com/eicar'
    response_url = 'mock://example.com/response'
    eicar_sha356 = '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'
    # Setup http mocks
    requests_mock.get(artifact_url, text=EICAR_STRING.decode('utf-8'))
    requests_mock.post(response_url, text='Success')
    bounty = Bounty(guid='test_valid_bounty_to_api',
                    artifact_type='FILE',
                    artifact_url=artifact_url,
                    sha256=eicar_sha356,
                    mimetype='text/plain',
                    expiration=datetime.datetime.now().isoformat(),
                    phase='assertion_window',
                    response_url=response_url,
                    rules=[]
                    )
    headers = {'X-POLYSWARM-EVENT': 'bounty'}
    response = client.post('/', headers=headers, json=dataclasses.asdict(bounty))

    assert response.status_code == 200


def test_invalid_bounty_to_api():
    client = app.test_client()

    headers = {'X-POLYSWARM-EVENT': 'bounty'}
    response = client.post('/', headers=headers, data={'asdf': 'fdsa'})

    assert response.status_code == 400