import base64
import enum
import dataclasses
import requests

from celery import Celery
from typing import Any, Dict

from microenginewebhookpy.settings import BROKER
from microenginewebhookpy.wsgi import Bounty

celery_app = Celery('tasks', broker=BROKER)

EICAR_STRING = base64.b64decode(
   b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


class Verdict(enum.Enum):
    BENIGN = 0
    MALICIOUS = 1
    SUSPICIOUS = 2
    UNKNOWN = 3


@dataclasses.dataclass
class ScanResult:
    verdict: Verdict
    confidence: float
    metadata: Dict[str, Any]


@celery_app.task
def scan(bounty: Bounty):
    session = requests.Session()
    with session.get(bounty.artifact_url) as response:
        response.raise_for_status()
        content = response.content

    if content == EICAR_STRING:
        scan_result = ScanResult(verdict=Verdict.MALICIOUS, confidence=1.0, metadata={'malware_family': 'EICAR-TEST-FILE'})
    else:
        scan_result = ScanResult(Verdict.BENIGN, 1.0, {})

    with session.post(bounty.response_url, json=dataclasses.asdict(scan_result)) as response:
        response.raise_for_status()
