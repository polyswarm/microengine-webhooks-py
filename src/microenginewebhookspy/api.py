import dataclasses
import enum
import logging

import requests
from flask import request, jsonify, Blueprint
from typing import List, Dict, Any

from microenginewebhookspy import scan

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


@dataclasses.dataclass
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


@api.route('/', method='POST')
def bounty_request_handler():
    event_name = request.headers.get(POLYSWARM_EVENT_NAME_HEADER, '').lower()

    if event_name == 'bounty':
        try:
            bounty = Bounty(**request.json)
            scan.delay(bounty)
        except (KeyError, ValueError):
            logger.exception('Bad Request')
            return jsonify('Bad Request'), 400

    return jsonify('OK'), 200
