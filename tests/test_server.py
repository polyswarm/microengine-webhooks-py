import datetime
import logging
import pytest

from polyswarm_engine.bounty import Bounty, forge_local_bounty


def test_valid_bounty_to_api(mocker, wsgi_app):
    mock_deliver = mocker.patch('polyswarm_engine.wsgi.backend._deliver', return_value=None)

    client = wsgi_app

    bounty: Bounty = forge_local_bounty(
        artifact_type='FILE',
        data=b'test',
        mimetype='text/plain',
        expiration=datetime.timedelta(seconds=300),
        min_allowed_bid=1,
        max_allowed_bid=1000,
    )
    environ_overrides = {'HTTP_X_POLYSWARM_EVENT': 'bounty'}
    response = client.post('/eicar-sample', json=bounty, environ_overrides=environ_overrides)

    assert response.status_code == 202
    mock_deliver.assert_called_once()


def test_invalid_bounty_to_api(wsgi_app):
    client = wsgi_app

    # Silencing expected log about the failure to parse this data
    logging.disable(logging.CRITICAL)
    environ_overrides = {'HTTP_X_POLYSWARM_EVENT': 'bounty'}
    response = client.post(
        '/eicar-sample',
        data='{"broken": ',
        content_type='application/json',
        environ_overrides=environ_overrides,
    )
    logging.disable(logging.NOTSET)

    assert str(response.status_code).startswith('4') # 4XX
