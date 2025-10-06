import os
from logging.config import dictConfig

from microenginewebhookspy.utils import to_wei

BROKER = os.environ.get('CELERY_BROKER_URL')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')

MAX_BID_RULE_NAME = os.environ.get('MAX_BID_RULE_NAME', 'max_allowed_bid')
MIN_BID_RULE_NAME = os.environ.get('MIN_BID_RULE_NAME', 'min_allowed_bid')
DEFAULT_MAX_BID = os.environ.get('DEFAULT_MAX_BID', to_wei(1))
DEFAULT_MIN_BID = os.environ.get('DEFAULT_MIN_BID', to_wei(1) / 16)

# Metrics values
DATADOG_API_KEY = os.environ.get('DATADOG_API_KEY')
DATADOG_APP_KEY = os.environ.get('DATADOG_APP_KEY')
ENGINE_NAME = os.environ.get('ENGINE_NAME', 'microengine-webhooks-py')
POLY_WORK = os.environ.get('POLY_WORK', 'local')

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'text')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'text': {
            'format': '%(asctime)s [%(levelname)s] (%(name)s): %(message)s',
        },
        'json': {
            'format': '%(level) %(name) %(timestamp) %(message)',
            'class': 'microenginewebhookspy.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': LOG_FORMAT,
        },
    },
    'loggers': {
        'celery': {
            'level': LOG_LEVEL,
        },
        'microenginewebhookspy': {
            'level': LOG_LEVEL,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    }
}

dictConfig(LOGGING)
