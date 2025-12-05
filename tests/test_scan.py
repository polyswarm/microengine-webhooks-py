import datetime



from polyswarm_engine.bounty import forge_local_bounty
from polyswarm_engine.bidutils import to_wei
from polyswarm_engine.constants import BENIGN, MALICIOUS
from microenginewebhookspy.engine import engine

from tests import EICAR_STRING


def test_scan_file_malicious(requests_mock):
    response_url = 'mock://example.com/response'
    # Setup http mocks
    requests_mock.post(response_url, text='Success')

    bounty = forge_local_bounty(artifact_type='FILE',
                                data=EICAR_STRING,
                                mimetype='text/plain',
                                expiration=datetime.timedelta(seconds=300),
                                min_allowed_bid=to_wei(1) / 16,
                                max_allowed_bid=to_wei(1),
                                )
    bounty['id'] = 12345678
    bounty['response_url'] = response_url

    with engine.create_backend() as backend:
        backend.update_analysis_environment()
        backend._deliver = backend._http_deliver
        backend.process_bounty(bounty)

    # Not testing metadata, since it may change version over version
    posted_json = requests_mock.last_request.json()
    assert posted_json['verdict'] == MALICIOUS


def test_scan_file_benign(requests_mock):
    response_url = 'mock://example.com/response'
    # Setup http mocks
    requests_mock.post(response_url, text='Success')

    bounty = forge_local_bounty(artifact_type='FILE',
                                data=b'this is benign file',
                                mimetype='text/plain',
                                expiration=datetime.timedelta(seconds=300),
                                min_allowed_bid=to_wei(1) / 16,
                                max_allowed_bid=to_wei(1),
                                )
    bounty['id'] = 23456789
    bounty['response_url'] = response_url

    with engine.create_backend() as backend:
        backend.update_analysis_environment()
        backend._deliver = backend._http_deliver
        backend.process_bounty(bounty)

    # Not testing metadata, since it may change version over version
    posted_json = requests_mock.last_request.json()
    assert posted_json['verdict'] == BENIGN
