import dataclasses
import enum
import logging
import requests

from flask import request, jsonify, Blueprint
from typing import List, Dict, Any

from microenginewebhookspy.settings import API_KEY

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
    bid: int
    metadata: Dict[str, Any]
    verdict_str: str = dataclasses.field(init=False)

    def __post_init__(self, verdict):
        self.verdict_str = verdict.value

    def __eq__(self, other):
        return isinstance(other, ScanResult) and other.verdict_str == self.verdict_str \
             and other.bid == self.bid and other.metadata == self.metadata

    def __hash__(self):
        calculated_hash = 7
        calculated_hash = 53 * calculated_hash + hash(self.verdict_str)
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
    rules: List[str]

    def fetch_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_url) as response:
            response.raise_for_status()
            return response.content

    def post_scan_result(self, scan_result: ScanResult):
        session = requests.Session()
        headers = {
            'Authorization': API_KEY
        }
        with session.post(self.response_url, headers=headers, json=dataclasses.asdict(scan_result)) as response:
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)


@api.route('/', methods=['POST'])
def bounty_request_handler():
    from microenginewebhookspy.scan import scan
    event_name = request.headers.get(POLYSWARM_EVENT_NAME_HEADER, '').lower()

    if event_name == 'bounty':
        try:
            body = request.get_json()
            bounty = Bounty(**body)
            logger.debug('Kicking off new scan with %s', bounty)
            scan.delay(dataclasses.asdict(bounty))
            return jsonify(''), 202
        except (TypeError, KeyError, ValueError):
            logger.exception('Bad Request')
            return jsonify({'bounty': 'Invalid bounty request'}), 400
    if event_name == 'ping':
        return jsonify(''), 200
    else:
        return jsonify({'X-POLYSWARM-EVENT': f'Given event not supported'}), 400

