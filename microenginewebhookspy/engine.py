#!/usr/bin/env python3
__version__ = '0.0.1'

import base64

import psengine


engine = psengine.EngineManager(name='eicar-sample', vendor='sample-vendorname')

EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


@engine.register_analyzer
def analyze(bounty):
    contents = psengine.get_artifact_bytes(bounty)
    if EICAR_STRING in contents:
        return {
            'verdict': psengine.MALICIOUS,
            'bid': psengine.bid_max(bounty),
            'metadata': {'malware_family': 'EICAR', 'confidence': 1.0},
        }
    else:
        return {
            'verdict': psengine.BENIGN,
            'bid': psengine.bid_max(bounty),
            'metadata': {},
        }


if __name__ == '__main__':
    engine.cli()
