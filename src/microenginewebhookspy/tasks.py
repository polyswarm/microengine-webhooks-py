from celery import Celery, Task
from microengine_utils import errors
from microengine_utils.datadog import configure_metrics
from microengine_utils.constants import SCAN_FAIL, SCAN_SUCCESS, SCAN_TIME, SCAN_VERDICT

from microenginewebhookspy.models import Bounty, ScanResult, Verdict, Assertion, Phase
from microenginewebhookspy import settings
from microenginewebhookspy.scan import scan, compute_bid


celery_app = Celery('tasks', broker=settings.BROKER)


class MetricsTask(Task):
    _metrics = None

    @property
    def metrics(self):
        if self._metrics is None:
            self._metrics = configure_metrics(
                settings.DATADOG_API_KEY,
                settings.DATADOG_APP_KEY,
                settings.ENGINE_NAME,
                poly_work=settings.POLY_WORK
            )

        return self._metrics


@celery_app.task(base=MetricsTask)
def handle_bounty(bounty):
    bounty = Bounty(**bounty)
    scan_result = ScanResult()
    with handle_bounty.metrics.timer(SCAN_TIME):
        try:
            scan_result = scan(bounty)
            handle_bounty.metrics.increment(SCAN_SUCCESS, tags=[f'type:{bounty.artifact_type}'])
            handle_bounty.metrics.increment(SCAN_VERDICT, tags=[f'type:{bounty.artifact_type}',
                                                                f'verdict:{scan_result.verdict.value}'])
        except errors.HighCompressionScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:highcompression']
            )
        except errors.EncryptedFileScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:encryptedfile']
            )
        except errors.CorruptFileScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:corruptfile']
            )
        except errors.FileSkippedScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:fileskipped']
            )
        except errors.ServerNotReadyScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:servernotready']
            )
        except errors.CalledProcessScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:calledprocess']
            )
        except errors.UnprocessableScanError:
            handle_bounty.metrics.increment(
                SCAN_FAIL, tags=[f'type:{bounty.artifact_type}', 'scan_error:unprocessable']
            )

    if bounty.phase == Phase.ARBITRATION:
        scan_response = scan_result.to_vote()
    else:
        if scan_result.verdict in [Verdict.UNKNOWN, Verdict.SUSPICIOUS]:
            # These results don't bid any NCT.
            bid = 0
        else:
            bid = compute_bid(bounty, scan_result)
        scan_response = scan_result.to_assertion(bid)

    bounty.post_response(scan_response)
