import base64

from celery import Celery

from microenginewebhookspy.api import Bounty, ScanResult, Verdict
from microenginewebhookspy.settings import BROKER
from microenginewebhookspy.utils import to_wei

celery_app = Celery('tasks', broker=BROKER)

EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


@celery_app.task
def scan(bounty):
    bounty = Bounty(**bounty)
    if bounty.artifact_type.lower() != 'file':
        scan_result = ScanResult(Verdict.UNKNOWN, to_wei(1), {})
        bounty.post_scan_result(scan_result)

    content = bounty.fetch_artifact()
    if content == EICAR_STRING:
        scan_result = ScanResult(Verdict.MALICIOUS, to_wei(1), {'malware_family': 'EICAR-TEST-FILE'})
    else:
        scan_result = ScanResult(Verdict.BENIGN, to_wei(1), {})

    bounty.post_scan_result(scan_result)
