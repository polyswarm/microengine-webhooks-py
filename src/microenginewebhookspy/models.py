import contextlib
import logging
import dataclasses
import enum
import requests

from typing import Dict, Any, Optional, Union
from polyswarmartifact.schema import ScanMetadata


logger = logging.getLogger(__name__)


class Phase(enum.Enum):
    ASSERTION = 'assertion'
    ARBITRATION = 'arbitration'


class Verdict(enum.Enum):
    BENIGN = 'benign'
    MALICIOUS = 'malicious'
    SUSPICIOUS = 'suspicious'
    UNKNOWN = 'unknown'


@dataclasses.dataclass
class Assertion:
    verdict: str
    bid: int
    metadata: Dict


@dataclasses.dataclass
class Vote:
    verdict: str
    metadata: Dict


@dataclasses.dataclass
class ScanResult:
    verdict: Verdict = dataclasses.field(default=Verdict.UNKNOWN)
    metadata: ScanMetadata = dataclasses.field(default_factory=lambda: ScanMetadata().set_malware_family(''))
    confidence: float = dataclasses.field(default=1.0)

    def to_assertion(self, bid: int = 0):
        return Assertion(self.verdict.value, bid, self.metadata.dict())

    def to_vote(self):
        return Vote(self.verdict.value, self.metadata.dict())


@dataclasses.dataclass(frozen=True)
class Bounty:
    id: int
    artifact_type: str
    artifact_uri: str
    expiration: str
    response_url: str
    rules: Dict[str, Any]
    sha256: Optional[str] = None
    mimetype: Optional[str] = None
    phase: Optional[str] = None
    metadata: Optional[dict] = None

    def fetch_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_uri) as response:
            response.raise_for_status()
            return response.content

    def post_response(self, scan_response: Union[Vote, Assertion]):
        wrapper = _set_http_debug if logger.getEffectiveLevel() >= logging.DEBUG else contextlib.nullcontext

        session = requests.Session()
        with wrapper(), session.post(self.response_url, json=dataclasses.asdict(scan_response)) as response:
            if logger.getEffectiveLevel() >= logging.DEBUG:
                logger.debug('request body: %s', response.request.body)
                logger.debug('response body: %s', response.text)
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)


@contextlib.contextmanager
def _set_http_debug():
    """
    Produce logs of HTTP calls

    Produces logs by manipulating `http.client.HTTPConnetion`,
    as suggested on https://github.com/urllib3/urllib3/issues/107#issuecomment-11690207
    """
    # You'll need to do this before urllib3 creates any http connection objects
    import http.client

    initial_debuglevel = http.client.HTTPConnection.debuglevel
    http.client.HTTPConnection.debuglevel = 5
    try:
        yield
    finally:
        http.client.HTTPConnection.debuglevel = initial_debuglevel
