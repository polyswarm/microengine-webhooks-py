#!/usr/bin/env python3
__version__ = '1.0'

import logging
import base64
import psengine

log = logging.getLogger(__name__)

engine = psengine.EngineManager(name='eicar-sample', vendor='sample-vendorname')

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
def analyze(bounty: psengine.Bounty) -> psengine.Analysis:
    contents = psengine.get_artifact_bytes(bounty)

    if EICAR_STRING in contents:
        verdict = psengine.MALICIOUS
        metadata = {'malware_family': 'EICAR', 'confidence': 1.0}
    else:
        verdict = psengine.BENIGN
        metadata = {}

    return {
        'verdict': verdict,
        'bid': psengine.bid_max(bounty),
        'metadata': metadata,
    }


if __name__ == '__main__':
    engine.cli()
