import dataclasses
import enum
import json
import logging
import requests

from flask import request, jsonify, Blueprint
from typing import List, Dict, Any

POLYSWARM_EVENT_NAME_HEADER = 'X-POLYSWARM-EVENT'

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)


class Verdict(enum.Enum):
    BENIGN = 'benign'
    MALICIOUS = 'malicious'
    SUSPICIOUS = 'suspicious'
    UNKNOWN = 'unknown'


@dataclasses.dataclass
class ScanResult:
    verdict: dataclasses.InitVar[Verdict]
    confidence: float
    metadata: Dict[str, Any]
    verdict_str: str = dataclasses.field(init=False)

    def __post_init__(self, verdict):
        self.verdict_str = verdict.value

    def __eq__(self, other):
        return isinstance(other, ScanResult) and other.verdict_str == self.verdict_str \
             and other.confidence == self.confidence and other.metadata == self.metadata

    def __hash__(self):
        calculated_hash = 7
        calculated_hash = 53 * calculated_hash + hash(self.verdict_str)
        calculated_hash = 53 * calculated_hash + hash(self.confidence)
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
    rules: List[str]

    def download_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_url) as response:
            response.raise_for_status()
            return response.content

    def send_assertion(self, scan_result: ScanResult):
        session = requests.Session()
        with session.post(self.response_url, json=dataclasses.asdict(scan_result)) as response:
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)


@api.route('/', methods=['POST'])
def bounty_request_handler():
    from microenginewebhookspy.scan import scan
    event_name = request.headers.get(POLYSWARM_EVENT_NAME_HEADER, '').lower()

    if event_name == 'bounty':
        try:
            bounty = Bounty(**json.loads(request.get_data()))
            scan.delay(dataclasses.asdict(bounty))
        except (KeyError, ValueError):
            logger.exception('Bad Request')
            return jsonify('Bad Request'), 400

    return jsonify('OK'), 200
