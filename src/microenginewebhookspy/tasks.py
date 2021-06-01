from celery import Celery

from microenginewebhookspy.models import Bounty, ScanResult, Verdict, Assertion, Phase
from microenginewebhookspy import settings
from microenginewebhookspy.scan import scan, compute_bid

celery_app = Celery('tasks', broker=settings.BROKER)


@celery_app.task
def handle_bounty(bounty):
    bounty = Bounty(**bounty)
    scan_result = scan(bounty)

    if bounty.phase == Phase.ARBITRATION or scan_result.verdict in [Verdict.UNKNOWN, Verdict.SUSPICIOUS]:
        # These results don't bid any NCT.
        bid = 0
    else:
        bid = compute_bid(bounty, scan_result)

    bounty.post_assertion(scan_result.to_assertion(bid))
