import dataclasses
import enum
import requests

from typing import List, Dict, Any, Optional
from polyswarmartifact.schema import Verdict as AssertionMetadata

from microenginewebhookspy.settings import API_KEY

class Verdict(enum.Enum):
    BENIGN = 'benign'
    MALICIOUS = 'malicious'
    SUSPICIOUS = 'suspicious'
    UNKNOWN = 'unknown'


@dataclasses.dataclass
class ScanResult:
    verdict: Verdict
    metadata: AssertionMetadata
    confidence: float = dataclasses.field(default=1)


@dataclasses.dataclass
class Assertion:
    verdict: str
    bid: Optional[int]
    metadata: Dict


    @classmethod
    def from_scan_result(cls, scan_result: ScanResult, bid: int=0):
        return cls(scan_result.verdict.value, bid, scan_result.metadata.dict())

    def __eq__(self, other):
        return isinstance(other, Assertion) and other.verdict == self.verdict\
             and other.bid == self.bid and other.metadata == self.metadata

    def __hash__(self):
        calculated_hash = 7
        calculated_hash = 53 * calculated_hash + hash(self.verdict)
        calculated_hash = 53 * calculated_hash + hash(self.bid)
        # Cannot hash a dict
        return calculated_hash


@dataclasses.dataclass(frozen=True)
class Bounty:
    guid: str
    artifact_type: str
    artifact_url: str
    sha256: str
    mimetype: str
    expiration: str
    phase: str
    response_url: str
    rules: Dict[str, Any]

    def fetch_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_url) as response:
            response.raise_for_status()
            return response.content

    def post_assertion(self, assertion: Assertion):
        session = requests.Session()
        headers = {
            'Authorization': API_KEY
        }
        with session.post(self.response_url, headers=headers, json=dataclasses.asdict(assertion)) as response:
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)
