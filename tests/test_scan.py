import dataclasses
import datetime

from microenginewebhookspy.models import Bounty, Verdict, Assertion
from microenginewebhookspy.utils import to_wei
from microenginewebhookspy.scan import EICAR_STRING
from microenginewebhookspy.tasks import handle_bounty

from polyswarmartifact.schema import Verdict as Metadata


def test_scan_malicious(requests_mock, mocker):
    # Setup mock assertion
    spy = mocker.spy(Bounty, 'post_assertion')
    artifact_url = 'mock://example.com/eicar'
    response_url = 'mock://example.com/response'
    eicar_sha256 = '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'
    # Setup http mocks
    requests_mock.get(artifact_url, text=EICAR_STRING.decode('utf-8'))
    requests_mock.post(response_url, text='Success')

    metadata = Metadata()
    metadata.malware_family = 'EICAR-TEST-FILE'

    bounty = Bounty(guid='test_scan_malicious',
                    artifact_type='FILE',
                    artifact_url=artifact_url,
                    sha256=eicar_sha256,
                    mimetype='text/plain',
                    expiration=datetime.datetime.now().isoformat(),
                    phase='assertion_window',
                    response_url=response_url,
                    rules={
                        'max_allowed_bid': 1 * 10 ** 18,
                        'min_allowed_bid': 1 * 10 ** 18 / 16,
                    }
                    )

    handle_bounty(dataclasses.asdict(bounty))
    metadata = Metadata()
    metadata.malware_family = 'EICAR-TEST-FILE'
    expected_result = Assertion(Verdict.MALICIOUS.value, to_wei(1), metadata.dict())
    spy.assert_called_once_with(bounty, expected_result)


def test_scan_benign(requests_mock, mocker):
    # Setup mock assertion
    spy = mocker.spy(Bounty, 'post_assertion')
    artifact_url = 'mock://example.com/not-eicar'
    response_url = 'mock://example.com/response'
    eicar_sha256 = '09688de240a0b492aca7af12057b7f24cd5d0439f14d40b9eec1ce920bc82cb6'
    # Setup http mocks
    requests_mock.get(artifact_url, text='not-eicar')
    requests_mock.post(response_url, text='Success')

    bounty = Bounty(guid='test_scan_benign',
                    artifact_type='FILE',
                    artifact_url=artifact_url,
                    sha256=eicar_sha256,
                    mimetype='text/plain',
                    expiration=datetime.datetime.now().isoformat(),
                    phase='assertion_window',
                    response_url=response_url,
                    rules={
                        'max_allowed_bid': 1 * 10 ** 18,
                        'min_allowed_bid': 1 * 10 ** 18 / 16,
                    }
                    )

    metadata = Metadata()
    metadata.malware_family = ''
    handle_bounty(dataclasses.asdict(bounty))
    expected_result = Assertion(Verdict.BENIGN.value, to_wei(1), metadata.dict())
    spy.assert_called_once_with(bounty, expected_result)
