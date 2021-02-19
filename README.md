# microengine-webhooks-py

PolySwarm is changing from a websocket based bounty delivery to webhooks.
Webhooks give PolySwarm more control over who scans which artifacts, and reduces wasted bandwidth for microengines.

This project is a base webhook implementation for microengines that can be used as a base to build more complicated microengines.
It sets up a basic server, and responds to events with a preconfigured server, web framework, and celery tasks. 
Users should be able to hit the ground running and edit only one file with two functions to get started.

## How it works

PolySwarm will send HTTP POST requests to the webhook to transmit events.
Microengines need only to listen passively until a new event arrives.

Nginx Unit acts the base web server to receive events from the HTTP requests.
Unit has a simple interface to configure an application for handling the requests in a variety of languages and web frameworks.    
PolySwarm elected to use a Flask application in python.

The event requests are all parsed, and handled in python code.

Each event request includes three special headers; `X-POLYSWARM-EVENT`, `X-POLYSWARM-SIGNATURE`, and `X-POLYSWARM-DELIVERY`.

`X-POLYSWARM-SIGNATURE` is read by `ValidateSenderMiddleware` in `middleware.py`.
The signature is an hmac of the request body, signed by the shared secret that is generated during registration.
This process prevents other parties from sending bounties and stealing scans.

`X-POLYSWARM-EVENT` is read in the request handler to determine what behavior PolySwarm is triggering.
For example, a Microengine will check for `ping`, or `bounty`.
`ping` is PolySwarm testing that the Webhook server is up.
`bounty` is PolySwarm sending a bounty to the webhook for scanning.

Ping requests have an empty string as payload. 
Their entire purpose is to see if PolySwarm can connect, and send a request.


Bounty requests have all the information needed to scan and assert on an artifact. 
Here is a sample Bounty.

```json
{"guid": "7cb3067a-28a7-48fe-9f39-8de8cacb3955",
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
The `Assertion` is sent back to PolySwarm at `bounty.response_url`.


## Customizing a microengine

Customizing your engine is as simple as overwriting just 1-2 functions.
Inside `scan.py` there are two functions, `scan` and `compute_bid`.
Those functions exist so developers can substitute their own logic.

Both of these functions are called in synchronous code.
The use of Celery ensures the webserver is not blocked by scanning.
Developers of course can use async code, but they must use `asyncio` directly. 


To get started, copy this project however is conveinent. 
Developers can fork, download, or any other means to get the source code.
The code is licensed with MIT, which is considered a permissive license.


### Overwriting Scan

The scan function is the core of any microengine.
It takes in a `Bounty` for some artifact, and returns a `ScanResult`.
The method of scanning is entirely up to the developer according to their needs.

The signature for scan is as follows.
`def scan(bounty: Bounty) -> ScanResult:`.
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

The example code is a simple eicar scanner. 
It checks that the bounty is for a file, and compares the contents against the eicar string. 
`polyswarm-artifact` is used to simplify metadata generation, and file comparison.


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

More complex engines PolySwarm has developed use `subprocess` to execute some binary for scanning, or send the file to another service for scanning.
Developers have the whole python language at their disposal in this function and can scan however is appropriate for their use case.

#### Suspicious or Unknown


In the latest iteration of the PolySwarm marketplace more verdict results have been added.
Microengines can now respond with Suspicious or Unknown. 

Unknown is a tool to tell PolySwarm the engine is working, but it doesn't want to, or doesn't know how to scan a file. 
PolySwarm uses this to filter out dead engines. 
Make sure to respond to use this if the microengine is still running, but doesn't have a determination on the file.

Suspicious is a new way to give information about an artifact.
In situations where an engine has low confidence of an artifact being malicious, they can send suspicious.
This does not require a bid, so does not risk NCT.
This can reduce both false positives, and false negatives.

### Overwriting Bid


Bidding is an essential part of a microengine.
By default, `compute_bid` uses the confidence, treated as a percentage, to put the bid on a range from min to max.
The signature for the `compute_bid` function is as follows.
`def compute_bid(bounty: Bounty, scan_result: ScanResult) -> int:`

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

* `bounty` events should have a fast response, where the scanning is done asynchronously 
* `ping` events must yield a 2XX response
* Assertions must be sent as an HTTP POST request to `bounty.response_url`
* Assertion requests must include an `AUTHORIZATION` header where the value is the API_KEY
* All Requests to and from PolySwarm are json format
* Assertions must be in the following format

```json
{
  "verdict": "malicious", # Or one of "benign"  "unknown" "suspicious"
  "bid": 1000000000000000000, # Any number between min and max bid values
  "metadata": {} # A dict of metadata
}
```

### Local testing

Pytest is used for unit testing the python code. 
Run `pytest -s` to test all parts.

In addition, there is a Flask app used for integration tests.
Run the docker-compose file with `docker-compose -f docker/docker-compose up`.
Make POST requests to `http://localhost:5000/`.

Includes a few test routes. 

* `/test/bounty/` Sends either an malicious (eicar) or benign bounty to scan. Integration test will print received assertion.
* `/test/ping` Sends a ping event. 
* `/test/anayze` Sends an analyze event, for testing an event type microengines won't respond to.


## Registering the Engine

Go to `https://polyswarm.network`.
Log in or create an account.
Navigate to webhooks.
Create the webhook.
Run the `Test` while the webhook is up 

Now that the webhook is registered and verified, navigate to engines.
Create an Engine. 
Assign the just created Webhook to the Engine. 


## Deploying to kubernetes
 
The included Chart and Dockerfiles make it easy to deploy to kubernetes.

1. Run/Use a Celery Broker
1. Fill in a RELEASE_NAME in Makefile
1. Change HELM_VERSIOn to the name of your helm 3 binary
1. Fill in values and secrets in `chart/env/default`
1. `make install`
