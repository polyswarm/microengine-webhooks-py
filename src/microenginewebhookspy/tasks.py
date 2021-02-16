import base64

from celery import Celery

from microenginewebhookspy.models import Bounty, ScanResult, Verdict, Assertion
from microenginewebhookspy.settings import BROKER

celery_app = Celery('tasks', broker=BROKER)


MAX_BID_RULE = 'max_allowed_bid'
MIN_BID_RULE = 'min_allowed_bid'


@celery_app.task
def handle_bounty(bounty):
    bounty = Bounty(**bounty)
    scan_result = scan(bounty)
    bid = None

    max_bid = bounty.rules.get(MAX_BID_RULE, settings.DEFAULT_MAX_BID)
    min_bid = bounty.rules.get(MIN_BID_RULE, settings.DEFAULT_MIN_BID)

    if scan_result.verdict == Verdict.MALICIOUS or scan_result.verdict == Verdict.BENIGN:
        bid = bid(max_bid, min_bid, bounty, scan_result)

    bounty.post_assertion(Assertion(verdict=scan_result.verdict, metadata=scan_result.metadata, bid=bid))
