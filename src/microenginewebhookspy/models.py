import dataclasses
import enum
import requests

from typing import List, Dict, Any, Optional
from polyswarmartifact.schema import Verdict as ScanMetadata


class Verdict(enum.Enum):
    BENIGN = 'benign'
    MALICIOUS = 'malicious'
    SUSPICIOUS = 'suspicious'
    UNKNOWN = 'unknown'


@dataclasses.dataclass
class Assertion:
    verdict: str
    bid: Optional[int]
    metadata: Dict

    def __eq__(self, other):
        return isinstance(other, Assertion) and other.verdict == self.verdict\
             and other.bid == self.bid and other.metadata == self.metadata

    def __hash__(self):
        calculated_hash = 7
        calculated_hash = 53 * calculated_hash + hash(self.verdict)
        calculated_hash = 53 * calculated_hash + hash(self.bid)
        # Cannot hash a dict
        return calculated_hash


@dataclasses.dataclass
class ScanResult:
    verdict: Verdict
    metadata: ScanMetadata
    confidence: float = dataclasses.field(default=1)

    def to_assertion(self, bid: int = 0):
        return Assertion(self.verdict.value, bid, self.metadata.dict())


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

    def fetch_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_uri) as response:
            response.raise_for_status()
            return response.content

    def post_assertion(self, assertion: Assertion):
        session = requests.Session()
        with session.post(self.response_url, json=dataclasses.asdict(assertion)) as response:
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)
