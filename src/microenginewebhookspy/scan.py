import base64

from microenginewebhookspy.models import Bounty, ScanResult, Verdict
from microenginewebhookspy import settings

from polyswarmartifact.schema import ScanMetadata


EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


def scan(bounty: Bounty) -> ScanResult:
    content = bounty.fetch_artifact()
    metadata = ScanMetadata().set_malware_family('')
    if content == EICAR_STRING:
        metadata.set_malware_family('EICAR-Test-File')
        return ScanResult(verdict=Verdict.MALICIOUS, confidence=1.0, metadata=metadata)
    else:
        return ScanResult(verdict=Verdict.BENIGN, confidence=1.0, metadata=metadata)


def compute_bid(bounty: Bounty, scan_result: ScanResult) -> int:
    max_bid = bounty.rules.get(settings.MAX_BID_RULE_NAME, settings.DEFAULT_MAX_BID)
    min_bid = bounty.rules.get(settings.MIN_BID_RULE_NAME, settings.DEFAULT_MIN_BID)

    bid = min_bid + max(scan_result.confidence * (max_bid - min_bid), 0)
    bid = min(bid, max_bid)
    return bid
