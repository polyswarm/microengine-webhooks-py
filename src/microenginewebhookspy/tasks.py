from celery import Celery

from microenginewebhookspy.models import Bounty, ScanResult, Verdict, Assertion
from microenginewebhookspy import settings
from microenginewebhookspy.scan import scan, compute_bid

celery_app = Celery('tasks', broker=settings.BROKER)





@celery_app.task
def handle_bounty(bounty):
    bounty = Bounty(**bounty)
    scan_result = scan(bounty)
    bid = None

    if scan_result.verdict == Verdict.MALICIOUS or scan_result.verdict == Verdict.BENIGN:
        bid = compute_bid(bounty, scan_result)

    bounty.post_assertion(Assertion.from_scan_result(scan_result, bid))
