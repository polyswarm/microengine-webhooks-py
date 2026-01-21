#!/usr/bin/env python3
__version__ = '1.0'

import logging
import base64
import polyswarm_engine as ps

log = logging.getLogger(__name__)

engine = ps.EngineManager(name='eicar-sample', vendor='sample-vendorname')

EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


@engine.register_head
def head():
    return {
        'product': 'eicar-sample',
        'scanner': {'version': '1.0'}
    }


@engine.register_analyzer
def analyze(bounty: ps.Bounty) -> ps.Analysis:
    if not ps.bounty.is_file_artifact(bounty):
        log.error("Received non-file artifact bounty")
        return ps.bounty.UNSUPPORTED

    contents = ps.get_artifact_bytes(bounty)

    if EICAR_STRING in contents:
        verdict = ps.MALICIOUS
        metadata = {'malware_family': 'EICAR', 'confidence': 1.0}
    else:
        verdict = ps.BENIGN
        metadata = {}

    return {
        'verdict': verdict,
        'bid': ps.bid_max(bounty),
        'metadata': metadata,
    }


if __name__ == '__main__':
    engine.cli()
