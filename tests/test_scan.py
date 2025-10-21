import dataclasses
import datetime

from io import BytesIO

from psengine.bounty import forge_local_bounty
from psengine.constants import BENIGN, MALICIOUS
from microenginewebhookspy.utils import to_wei
from microenginewebhookspy.tasks import handle_bounty

from tests import EICAR_STRING


def test_scan_file_malicious(requests_mock):
    artifact_uri = 'mock://example.com/eicar'
    response_url = 'mock://example.com/response'
    eicar_sha256 = '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'
    # Setup http mocks
    requests_mock.get(artifact_uri, body=BytesIO(EICAR_STRING))
    requests_mock.post(response_url, text='Success')

    bounty = forge_local_bounty(artifact_type='FILE',
                                artifact_uri=artifact_uri,
                                sha256=eicar_sha256,
                                mimetype='text/plain',
                                expiration=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                min_allowed_bid=to_wei(1) / 16,
                                max_allowed_bid=to_wei(1),
                                )
    bounty['id'] = 12345678
    bounty['response_url'] = response_url

    handle_bounty(dataclasses.asdict(bounty))

    # Not testing metadata, since it may change version over version
    posted_json = requests_mock.last_request.json()
    assert posted_json['verdict'] == MALICIOUS


def test_scan_file_benign(requests_mock):
    artifact_uri = 'mock://example.com/not-eicar'
    response_url = 'mock://example.com/response'
    eicar_sha256 = '09688de240a0b492aca7af12057b7f24cd5d0439f14d40b9eec1ce920bc82cb6'
    # Setup http mocks
    requests_mock.get(artifact_uri, text='not-eicar')
    requests_mock.post(response_url, text='Success')

    bounty = forge_local_bounty(artifact_type='FILE',
                                artifact_uri=artifact_uri,
                                sha256=eicar_sha256,
                                mimetype='text/plain',
                                expiration=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                min_allowed_bid=to_wei(1) / 16,
                                max_allowed_bid=to_wei(1),
                                )
    bounty['id'] = 23456789
    bounty['response_url'] = response_url

    handle_bounty(dataclasses.asdict(bounty))

    # Not testing metadata, since it may change version over version
    posted_json = requests_mock.last_request.json()
    assert posted_json['verdict'] == BENIGN
