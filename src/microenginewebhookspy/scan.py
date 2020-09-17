import base64

from celery import Celery

from microenginewebhookspy.settings import BROKER
from microenginewebhookspy.api import Bounty, ScanResult, Verdict

celery_app = Celery('tasks', broker=BROKER)

EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


@celery_app.task
def scan(bounty):
    bounty = Bounty(**bounty)
    if bounty.artifact_type.lower() != 'file':
        scan_result = ScanResult(Verdict.UNKNOWN, 1.0, {})
        bounty.post_scan_result(scan_result)

    content = bounty.download_artifact()
    if content == EICAR_STRING:
        scan_result = ScanResult(Verdict.MALICIOUS, 1.0, {'malware_family': 'EICAR-TEST-FILE'})
    else:
        scan_result = ScanResult(Verdict.BENIGN, 1.0, {})

    bounty.post_scan_result(scan_result)
