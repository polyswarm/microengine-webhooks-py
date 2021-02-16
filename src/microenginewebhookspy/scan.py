from microenginewebhookspy.models import Bounty, ScanResult, Assertion, Verdict
from microenginewebhookspy.utils import to_wei
from microenginewebhookspy import settings

from polyswarmartifact.schema import Verdict as Metadata
from polyswarmartifact.artifact_type import ArtifactType



EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


def scan(bounty: Bounty) -> ScanResult:
    metadata = Metadata()
    metadata.malware_family = ''
    if bounty.artifact_type.lower() != ArtifactType.FILE.value:
        scan_result = ScanResult(verdict=Verdict.UNKNOWN, confidence=0, metadata=metadata)
        bounty.post_scan_result(scan_result)

    content = bounty.fetch_artifact()
    if content == EICAR_STRING:
        metadata.malware_family = 'EICAR-TEST-FILE'
        scan_result = ScanResult(verdict=Verdict.MALICIOUS, confidence=1, metadata=metadata)
    else:
        scan_result = ScanResult(verdict=Verdict.BENIGN, confidence=1, metadata=metadata)


def bid(max_bid, min_bid, bounty: Bounty, scan_result: ScanResult) -> int:
    bid = min_bid + max(confidence * (max_bid - min_bid), 0)
    bid = min(bid, max_bid)
    return bid
