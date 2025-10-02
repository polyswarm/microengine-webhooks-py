# microengine-webhooks-py

PolySwarm is changing from a websocket based bounty delivery to webhooks.
Webhooks reduce wasted bandwidth by sending only relevant bounty events to each engine.

This project has a simple webhook microengine that can be used as a base to build more complicated microengines.
Users should be able to quickly get running by editing only one file with two functions to get started.

## How it works

PolySwarm will send events as HTTP POST requests to the webhook.
Microengines need only to listen passively until a new event arrives.

Nginx Unit acts as the base web server to receive HTTP requests.
A python Flask application runs with Unit to handle the requests.
The event requests are all parsed, and handled in python code.

Each event request includes three special headers; `X-POLYSWARM-EVENT`, `X-POLYSWARM-SIGNATURE`, and `X-POLYSWARM-DELIVERY`.

`X-POLYSWARM-SIGNATURE` is read by `ValidateSenderMiddleware` in `middleware.py`.
The signature is an HMAC of the request body, signed by the shared secret that is generated during engine registration.
This process prevents other parties from sending bounties and stealing scans.

`X-POLYSWARM-EVENT` is read in the request handler to determine which feature the event triggers.
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
After that, it combines the `ScanResult`, and `bid`, into an `Assertion` or `Vote`.
The `Assertion` or `Vote` is sent back at `bounty.response_url`.


## Customizing a microengine

Customizing your engine is as simple as overriding just 1-2 functions.
Inside `scan.py` there are two functions, `scan` and `compute_bid`.
These functions are called in synchronous code.


To get started, clone, fork, or download this project, and move to the Overriding Scan section.


### Overriding Scan

The scan function is the core of any microengine.
It takes in a `Bounty` for some artifact, and returns a `ScanResult`.

The signature for scan is as follows.

`def scan(bounty: Bounty) -> ScanResult:`.

The example code is a simple EICAR scanner.
It checks that the bounty contains a file, and compares the contents against the EICAR string.
`polyswarm-artifact` is used to simplify metadata generation, and file comparison.

More complex engines use `subprocess` to execute some software for scanning, or send the file to another service for scanning.
Developers have the whole python language at their disposal to develop this function.

```python
import base64

from microenginewebhookspy.models import Bounty, ScanResult, Verdict

from polyswarmartifact.schema import ScanMetadata



EICAR_STRING = base64.b64decode(
    b'WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo='
)


def scan(bounty: Bounty) -> ScanResult:
    content = bounty.fetch_artifact()
    metadata = ScanMetadata().set_malware_family('')
    if content == EICAR_STRING:
        metadata.set_malware_family('EICAR-TEST-FILE')
        return ScanResult(verdict=Verdict.MALICIOUS, confidence=1.0, metadata=metadata)
    else:
        return ScanResult(verdict=Verdict.BENIGN, confidence=1.0, metadata=metadata)
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

    def post_response(self, scan_response: Union[Assertion, Vote]):
        session = requests.Session()
        with session.post(self.response_url, json=dataclasses.asdict(scan_response)) as response:
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

    def to_vote(self):
        return Vote(self.verdict.value, self.metadata.dict())
```

#### Suspicious or Unknown


In the latest iteration of the marketplace, more verdict options have been added.
Microengines can now assert with Suspicious, or Unknown verdicts, in addition to the original Malicious and Benign verdicts.

Unknown indicates that the engine is working, but doesn't have enough information to make a determination.
That could be the file isn't supported, it's taking to long to scan, or the engine just didn't want to scan it.
Engines that don't respond at all are considered failing.
Too many failures will pause the flow of bounties to the engine until the issue is resolved.
Make sure to use Unknown in all cases where the engine is unable to make a determination.

Suspicious is a new response that gives new information about an artifact.
It's ideal for situations where confidence is low, and an engine does not want to report false negatives, nor positives.


### Overriding Bid


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

For example, developers may want to do any of the following.

* Change the `metadata` field in `ScanResult` to use a `Dict` instead of polyswarm-artifact.
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
* All Requests to and from PolySwarm are json format.
* Assertions must match the schema.
* Votes must match the given schema.


**Assertions**

```json
{
  "verdict": "malicious",
  "bid": 1000000000000000000,
  "metadata": {}
}
```

**Votes**

```json
{
  "verdict": "malicious",
  "metadata": {}
}
```

### Local testing

Pytest is used for unit testing the python code.
Run `pytest -s` to start tests.

In addition, there is a Flask app used for integration tests.
Run the docker-compose file with `docker-compose -f docker/docker-compose up`.

To trigger integration tests, send POST requests to `http://localhost:5000/`.
There are several test routes that trigger webhooks to the microengine for testing.

* `/test/bounty` Sends either an malicious (EICAR) or benign bounty to scan. Integration test will print received scan response.
* `/test/ping` Sends a ping event.
* `/test/analyze` Sends an analyze event, for testing an event type microengines won't respond to.


## Deploying with containers

The included Dockerfiles have an example of how to deploy via nginx-unit using containers.
