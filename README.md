# microengine-webhooks-py

PolySwarm is changing from a websocket based bounty delivery to webhooks.
Webhooks reduce wasted bandwidth by sending only relevant bounty events to each engine.

This project has a simple webhook microengines that can be used as a base to build more complicated microengines.
Users should be able to hit the ground running and edit only one file with two functions to get started.

## How it works

PolySwarm will send events as HTTP POST requests to the webhook.
Microengines need only to listen passively until a new event arrives.

Nginx Unit acts the base web server to receive http requests.
A python Flask application runs with Unit to handle the requests.
The event requests are all parsed, and handled in python code.

Each event request includes three special headers; `X-POLYSWARM-EVENT`, `X-POLYSWARM-SIGNATURE`, and `X-POLYSWARM-DELIVERY`.

`X-POLYSWARM-SIGNATURE` is read by `ValidateSenderMiddleware` in `middleware.py`.
The signature is an hmac of the request body, signed by the shared secret that is generated during registration.
This process prevents other parties from sending bounties and stealing scans.

`X-POLYSWARM-EVENT` is read in the request handler to determine what feature the event triggers.
For example, a Microengine will check for `ping`, or `bounty`.
Ping tests that the Webhook server is up.
Bounty scans an artifact.

Ping requests have an empty string as payload.
Their entire purpose is to see if it is possible to connect, and send a request.


Bounty requests have all the information needed to scan and assert on an artifact.

Here is a sample Bounty.

```json
{
  "guid": "7cb3067a-28a7-48fe-9f39-8de8cacb3955",
  "artifact_type": "FILE",
  "artifact_url": "https://secure.eicar.org/eicar.com",
  "sha256": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
  "mimetype": "text/plain",
  "expiration": "2021-02-19T10:13:47.036168",
  "phase": "assertion",
  "response_url": "https://example.com/",
  "rules": {"min_allowed_bid": 62500000000000, "max_allowed_bid": 1000000000000000000}
}
```

The request_handler takes the entire json message and sends it to the `handle_bounty` task in Celery.
The `handle_bounty` task, in `tasks.py` coordinates scanning, and bidding.
It calls the `scan` function in `scan.py` to get a `ScanResult` object.
The `Bounty`, and `ScanResult` are passed to `compute_bid` which yields a final `bid`.
After that, it combines the `ScanResult`, and `bid`, into an `Assertion`.
The `Assertion` is sent back at `bounty.response_url`.


## Customizing a microengine

Customizing your engine is as simple as overwriting just 1-2 functions.
Inside `scan.py` there are two functions, `scan` and `compute_bid`.
These functions are called in synchronous code.


To get started, clone, fork, or download this project, and move to the Overwriting Scan section.


### Overwriting Scan

The scan function is the core of any microengine.
It takes in a `Bounty` for some artifact, and returns a `ScanResult`.

The signature for scan is as follows.

`def scan(bounty: Bounty) -> ScanResult:`.

The example code is a simple eicar scanner.
It checks that the bounty contains a file, and compares the contents against the eicar string.c
`polyswarm-artifact` is used to simplify metadata generation, and file comparison.

More complex engines use `subprocess` to execute some software for scanning, or send the file to another service for scanning.
Developers have the whole python language at their disposal to develop this function.

```python
import base64

from microenginewebhookspy.models import Bounty, ScanResult, Verdict

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
```

`Bounty` and `ScanResult` are defined in `src/microenginewebhookspy/models.py`.

**Bounty**
```python
@dataclasses.dataclass(frozen=True)
class Bounty:
    guid: str
    artifact_type: str
    artifact_url: str
    sha256: str
    mimetype: str
    expiration: str
    phase: str
    response_url: str
    rules: Dict[str, Any]

    def fetch_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_url) as response:
            response.raise_for_status()
            return response.content

    def post_assertion(self, assertion: Assertion):
        session = requests.Session()
        headers = {
            'Authorization': API_KEY
        }
        with session.post(self.response_url, headers=headers, json=dataclasses.asdict(assertion)) as response:
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)
```

**ScanResult**
```python
@dataclasses.dataclass
class ScanResult:
    verdict: Verdict
    metadata: ScanMetadata
    confidence: float = dataclasses.field(default=1)

    def to_assertion(self, bid: int = 0):
        return Assertion(self.verdict.value, bid, self.metadata.dict())
```

#### Suspicious or Unknown


In the latest iteration of the marketplace, more verdict options have been added.
Microengines can now assert with Suspicious, or Unknown verdicts.

Unknown indicates that the engine is working, but doesn't have enough information to make an assertion.
That could be the file isn't supported, it's taking to long to scan, or the engine just didn't want to scan it.
Engines that don't respond at all are considered failing.
Too many failures will pause the flow of bounties to the engine until the issue is resolved.
Make sure to use Unknown in all cases where the engine is unable to make a determination.

Suspicious is a new response that gives new information about an artifact.
It's ideal for situations where confidence is low, and an engine does not want to report false negatives, nor positives.


### Overwriting Bid


By default, `compute_bid` uses the confidence, treated as a percentage, to put the bid on a range from min to max.
The return value here is an integer, where 1 NCT is 1000000000000000000.


```python
from microenginewebhookspy.models import Bounty, ScanResult
from microenginewebhookspy import settings


def compute_bid(bounty: Bounty, scan_result: ScanResult) -> int:
    max_bid = bounty.rules.get(settings.MAX_BID_RULE_NAME, settings.DEFAULT_MAX_BID)
    min_bid = bounty.rules.get(settings.MIN_BID_RULE_NAME, settings.DEFAULT_MIN_BID)

    bid = min_bid + max(scan_result.confidence * (max_bid - min_bid), 0)
    bid = min(bid, max_bid)
    return bid
```


### Everything is customizable

Everything in this project is customizable.
This marks a change from polyswarm-client, where developers just created a module to run inside polyswarm-client.

For example, a developers may want to do any of the following.

* Change the `metadata` field in `ScanResult` to use a `Dict` instead of polyswarm-artifact (Will require a change in `ScanResult.to_assertion` as well).
* Add more fields in `ScanResult` that `compute_bid` uses to generate a bid.
* Remove `Celery` in favor of another asynchronous execution solution.
* Change from Flask to Django, or another web framework.
* Change languages.
* Change webserver to uWSGI, or gunicorn


### Microengine Requirements

While this project is meant to be customizable, there are still a few requirements that must be met.

* `bounty` events should have a fast response, where the scanning is done asynchronously.
* `ping` events must respond with a 2XX status.
* Assertions must be sent as an HTTP POST request to `bounty.response_url`.
* Assertion requests must include an `AUTHORIZATION` header where the value is the engine's `API_KEY`.
* All Requests to and from PolySwarm are json format.
* Assertions must be in the format below.

```json
{
  "verdict": "malicious", # Or one of "benign"  "unknown" "suspicious"
  "bid": 1000000000000000000, # Any number between min and max bid values
  "metadata": {} # A dict of metadata
}
```

### Local testing

Pytest is used for unit testing the python code.
Run `pytest -s` to start tests.

In addition, there is a Flask app used for integration tests.
Run the docker-compose file with `docker-compose -f docker/docker-compose up`.

To trigger integration tests, send POST requests to `http://localhost:5000/`.
There are several test routes that trigger webhooks to the microengine for testing.

* `/test/bounty/` Sends either an malicious (eicar) or benign bounty to scan. Integration test will print received assertion.
* `/test/ping` Sends a ping event.
* `/test/anayze` Sends an analyze event, for testing an event type microengines won't respond to.


## Registering the Engine

1. Go to `https://polyswarm.network`.
1. Log in or create an account.
1. Navigate to webhooks.
1. Register the webhook.
1. Run the webhook test.
1. Register the engine.
1. Assign the new webhook to the engine.


## Deploying to kubernetes

The included Chart and Dockerfiles make it easy to deploy to kubernetes.
The steps below assume you have already configured helm 3 and kubernetes.

1. Run/Use a Celery Broker.
1. Fill in a `RELEASE_NAME` in Makefile.
1. Change `HELM_VERSION` to the name of your helm 3 binary in your path.
1. Fill in values and secrets in `chart/env/default`.
1. `make install`.
