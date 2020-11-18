import dataclasses
import datetime

from microenginewebhookspy.api import Bounty, Verdict, ScanResult
from microenginewebhookspy.utils import to_wei
from microenginewebhookspy.scan import EICAR_STRING, scan


def test_scan_malicious(requests_mock, mocker):
    # Setup mock assertion
    spy = mocker.spy(Bounty, 'post_scan_result')
    artifact_url = 'mock://example.com/eicar'
    response_url = 'mock://example.com/response'
    eicar_sha356 = '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f'
    # Setup http mocks
    requests_mock.get(artifact_url, text=EICAR_STRING.decode('utf-8'))
    requests_mock.post(response_url, text='Success')

    bounty = Bounty(guid='test_scan_malicious',
                    artifact_type='FILE',
                    artifact_url=artifact_url,
                    sha256=eicar_sha356,
                    mimetype='text/plain',
                    expiration=datetime.datetime.now().isoformat(),
                    phase='assertion_window',
                    response_url=response_url,
                    rules=[]
                    )

    scan(dataclasses.asdict(bounty))
    expected_result = ScanResult(Verdict.MALICIOUS, to_wei(1), {'malware_family': 'EICAR-TEST-FILE'})
    spy.assert_called_once_with(bounty, expected_result)


def test_scan_benign(requests_mock, mocker):
    # Setup mock assertion
    spy = mocker.spy(Bounty, 'post_scan_result')
    artifact_url = 'mock://example.com/not-eicar'
    response_url = 'mock://example.com/response'
    eicar_sha356 = '09688de240a0b492aca7af12057b7f24cd5d0439f14d40b9eec1ce920bc82cb6'
    # Setup http mocks
    requests_mock.get(artifact_url, text='not-eicar')
    requests_mock.post(response_url, text='Success')

    bounty = Bounty(guid='test_scan_benign',
                    artifact_type='FILE',
                    artifact_url=artifact_url,
                    sha256=eicar_sha356,
                    mimetype='text/plain',
                    expiration=datetime.datetime.now().isoformat(),
                    phase='assertion_window',
                    response_url=response_url,
                    rules=[]
                    )

    scan(dataclasses.asdict(bounty))
    expected_result = ScanResult(Verdict.BENIGN, to_wei(1), {})
    spy.assert_called_once_with(bounty, expected_result)


def test_scan_result_equal():
    assert ScanResult(Verdict.BENIGN, 10000000000000000, {}) == ScanResult(Verdict.BENIGN, 10000000000000000, {})
    assert ScanResult(Verdict.BENIGN, 10000000000000000, {}) != ScanResult(Verdict.BENIGN, 6250000000000, {})
