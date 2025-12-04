# microengine-webhooks-py

This project has a simple webhook microengine that can be used as a base to build more complicated microengines.
Users should be able to quickly get running by editing only one file with two functions to get started.

# Quickstart

## Install and test

Clone this repository.

`git clone https://github.com/polyswarm/microengine-webhooks-py.git`

Install the package in development mode to allow customization. We recommend using a [virtual environment](https://docs.python.org/3/library/venv.html).

`pip install -e .[web,gunicorn,tests]`

Check that the instalation is working correctly

```console
$ python -m microenginewebhookspy.engine analyze --check-eicar
{
  "metadata": {
    "product": "eicar-sample",
    "scanner": {
      "version": "1.0",
      "environment": {
        "operating_system": "Linux",
        "architecture": "x86_64"
      }
    },
    "malware_family": "EICAR",
    "confidence": 1.0
  },
  "verdict": "malicious",
  "bid": 999900000000000000
}
```

Run the tests

```console
$ pytest -v
================== test session starts ==================
(...)
configfile: pyproject.toml
plugins: requests-mock-1.12.1, mock-3.15.1
collected 4 items

tests/test_scan.py::test_scan_file_malicious PASSED [ 25%]
tests/test_scan.py::test_scan_file_benign PASSED  [ 50%]
tests/test_server.py::test_valid_bounty_to_api PASSED [ 75%]
tests/test_server.py::test_invalid_bounty_to_api PASSED [100%]
============= 4 passed, 4 warnings in 0.09s =============
```

Now you have a working Engine that detects EICAR as malware.

## Implementing your first engine

In `microenginewebhookspy/engine.py` there are two functions in less than
40 lines of code. The most important one is `analyze(bounty)`, which is where
to wire up the malware detection tool.

```py
# import polyswarm_engine as ps

@engine.register_analyzer
def analyze(bounty: ps.Bounty) -> ps.Analysis:
    contents = ps.get_artifact_bytes(bounty)

    if EICAR_STRING in contents:
        verdict = ps.MALICIOUS
        metadata = {'malware_family': 'EICAR', 'confidence': 1.0}
    else:
        verdict = ps.BENIGN
        metadata = {}

    return {
        'verdict': verdict
        'bid': ps.bid_max(bounty),
        'metadata': metadata,
    }
```

Your return dict will be checked against `polyswarm_engine.Analysis` rules,
e.g. a `verdict` is present and `metadata['confidence']` is a float
between 0.0 and 1.0 _if provided_.
For the full ruleset, have a peek at the `polyswarm_engine` codebase.

## Test your engine

During the implementation, you can issue ad-hoc tests calling the `python -m microenginewebhookspy.engine analyze` tool.
Alternatively, it also works by executing the file directly:

```console
$ cd microenginewebhookspy
$ ./engine.py analyze --help
Usage: eicar-sample analyze [OPTIONS] [ARTIFACTS]...

  Analyze artifacts

Options:
  -v, --verbose
  --check-empty     Verify this engine can analyze an empty
                                  bounty
  --check-eicar     Verify this engine can analyze EICAR test
                    file
  --check-wicar, --check-exploit-url
                    Verify this engine can analyze the WICAR
                    exploit kit URL
  -t, --artifact-type [bounty|file|url]
                    Artifact type to use when constructing
                    bounties. 'bounty' loads manually
                    constructed bounties, treating each argument
                    as the path to a JSON-encoded bounty object
--help              Show this message and exit.
```

The returned value will be checked for structure.

This CLI can issue scans for files in your disk, for local testing pourposes:

```console
$ ./engine.py analyze ~/Downloads/Firefox\ Installer.exe
{
  ...
  "verdict": "benign",
  "bid": 999900000000000000
}
```

We recommend that you always check scans for:
- EMPTY bounties
- EICAR if creating a file-scanning engines
- WICAR if creating a url-scanning engine
- Return UNKNOWN for unsupported file types

## Example: Checking the file type

If you run an analysis for WICAR the template implementation will return BENIGN:

```console
$ ./engine.py analyze --check-wicar
{
  ...
  "verdict": "benign",
  "bid": 999900000000000000
}
...
AssertionError: Received 'benign' instead of malicious
```

As an example, for handling URL bounties gracefully,
you can change the `engine.py` file to have these new lines:

```diff
# import polyswarm_engine as ps

 @engine.register_analyzer
 def analyze(bounty: ps.Bounty) -> ps.Analysis:
+    if not ps.bounty.is_file_artifact(bounty):
+        log.error("Received non-file artifact bounty")
+        return ps.bounty.UNSUPPORTED
     contents = ps.get_artifact_bytes(bounty)
```

It will now change to answer non-file bounties with an UNSUPPORTED verdict.

```console
$ ./engine.py analyze --check-wicar
2025-10-22 20:30:19,022 - ERROR [engine.py:28][analyze] Received non-file artifact bounty
{
  ...
  "verdict": "unknown",
  "bid": 0
}
...
AssertionError: Received 'unknown' instead of malicious
```

Which is fine for an EICAR engine, that is not supposed to handle URL bounties.

# Where to go from here?

This simple engine now does everything in the correct way.
Your existing malware-detection tool can be freely integrated within `engine.py`.

To help you get started, tooling exists inside the `polyswarm_engine` package.
For example, if your tool can natively scan files on the filesystem via CLI, there
is a context manager function that downloads the file and stores in a temporary
folder, making your life easier:

```diff
# import polyswarm_engine as ps

 @engine.register_analyzer
 def analyze(bounty: ps.Bounty) -> ps.Analysis:
-    contents = ps.get_artifact_bytes(bounty)
+    with ps.ArtifactTempfile(bounty) as path:
+        my_tool_do_handle_a_file(path)
```

That and other niceties are covered in full on the [PolySwarm Documentation](https://docs.polyswarm.io/suppliers),
specially on the PolySwarm Engine Package section: https://docs.polyswarm.io/suppliers/polyswarm-engine-package/

# How it works?

During the tests above the `engine.py analyze` tool simulated a Bounty
already received and enqueued for processing inside a Celery worker.
Then it calls the `analyze()` function with that Bounty "dict".

For real engines, PolySwarm will send events as HTTP POST requests
to your server webhook, configured in the PolySwarm website.
Engines need to listen passively until a new event arrives.

Your webserver will receive HTTP requests. A python WSGI application running
handles the requests and enqueues a job to be processed by a worker.

The worker runs your function `analyze()` and it decides the appropriate response.
In the same job the worker sends the response back to PolySwarm.

# How to run this for real?

More details about the workflow briefly explained above, recommendations and
alternatives for common scenarios are also available
in the [PolySwarm Documentation](https://docs.polyswarm.io/suppliers).


---
# MOVE TO DOCS :point-down:
---

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


#### Verdict meanings

Microengines can assert with Unknown verdicts, Malicious, Suspicious, or Benign.

Be aware that **Unknown** and **Suspicious** are purely informational verdicts
and produce zero bids and zero distribution of the artifact bounty during the
arbitration phase.

**Unknown** indicates that the engine is working, but doesn't have enough information to make a determination. Or that something unexpected occured and a verdict cannot be produced.
That could be the file isn't supported, it's taking to long to scan, or the engine just didn't want to scan it.

Make sure to use Unknown in all cases where the engine is unable to make a determination. Engines that don't respond at all are considered failing.
Too many failures should automatically pause the flow of bounties to the engine
until the issue is resolved.

**Malicious** is a response meaning that a malware is detected.
We recommend to provide the `malware_family` and a `confidence` value if available.

**Suspicious** is a response that gives new information about an artifact.
It's ideal for situations where confidence is low,
and an engine does not want to report false negatives, nor positives.

**Benign** is a response meaning that a malware was not detected.
We recommend to provide a `confidence` value if available.


### Overriding Bid
TBD

### Everything is customizable

Everything in this project is customizable.

For example, developers may want to do any of the following.
* Remove `Celery` in favor of another asynchronous execution solution.
* Change from Flask to Django, or another web framework.
* Change languages.
* Change webserver to uWSGI, or gunicorn


### Microengine Requirements

While this project is meant to be customizable, there are still a few requirements that must be met.

* `bounty` HTTP events should have a fast response,
deferring the scanning to bedone asynchronously.
* `ping` events must respond with a 2XX status.
* Assertions must be sent as an HTTP POST request to `bounty.response_url`.
* All Requests to and from PolySwarm are json format.
* Assertions must match the `polyswarm_engine.Analysis` schema.
* Votes must match the `polyswarm_engine.Analysis` schema.


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

In addition, there is a Flask app used for integration tests.
Run the docker-compose file with `docker-compose -f docker/docker-compose up`.

To trigger integration tests, send POST requests to `http://localhost:5000/`.
There are several test routes that trigger webhooks to the microengine for testing.

* `/test/bounty` Sends either an malicious (EICAR) or benign bounty to scan. Integration test will print received scan response.
* `/test/ping` Sends a ping event.
* `/test/analyze` Sends an analyze event, for testing an event type microengines won't respond to.


## Deploying with containers

The included Dockerfiles have an example of how to deploy via nginx-unit using containers.
