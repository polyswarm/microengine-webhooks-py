from celery import Celery, exceptions

from microenginewebhookspy.models import Bounty, ScanResult, Verdict, Assertion, Phase
from microenginewebhookspy import settings
from microenginewebhookspy.scan import scan, compute_bid

celery_app = Celery('tasks', broker=settings.BROKER)


@celery_app.task
def handle_bounty(bounty):
    bounty = Bounty(**bounty)
    try:
        scan_result = scan(bounty)
    except exceptions.SoftTimeLimitExceeded:
        scan_result = ScanResult()

    if bounty.phase == Phase.ARBITRATION:
        scan_response = scan_result.to_vote()
    else:
        if scan_result.verdict in [Verdict.UNKNOWN, Verdict.SUSPICIOUS]:
            # These results don't bid any NCT.
            bid = 0
        else:
            bid = compute_bid(bounty, scan_result)
        scan_response = scan_result.to_assertion(bid)

    bounty.post_response(scan_response)
