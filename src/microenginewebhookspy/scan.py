import base64

from microenginewebhookspy.models import Bounty, ScanResult, Verdict
from microenginewebhookspy import settings

from polyswarmartifact.schema import Verdict as ScanMetadata
from polyswarmartifact.artifact_type import ArtifactType



EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


def scan(bounty: Bounty) -> ScanResult:
    metadata = ScanMetadata()
    metadata.malware_family = ''
    if ArtifactType.from_string(bounty.artifact_type.lower()) != ArtifactType.FILE:
        return ScanResult(verdict=Verdict.UNKNOWN, confidence=0, metadata=metadata)

    content = bounty.fetch_artifact()
    if content == EICAR_STRING:
        metadata.malware_family = 'EICAR-TEST-FILE'
        return ScanResult(verdict=Verdict.MALICIOUS, confidence=1, metadata=metadata)
    else:
        return ScanResult(verdict=Verdict.BENIGN, confidence=1, metadata=metadata)


def compute_bid(bounty: Bounty, scan_result: ScanResult) -> int:
    max_bid = bounty.rules.get(settings.MAX_BID_RULE_NAME, settings.DEFAULT_MAX_BID)
    min_bid = bounty.rules.get(settings.MIN_BID_RULE_NAME, settings.DEFAULT_MIN_BID)

    bid = min_bid + max(scan_result.confidence * (max_bid - min_bid), 0)
    bid = min(bid, max_bid)
    return bid
