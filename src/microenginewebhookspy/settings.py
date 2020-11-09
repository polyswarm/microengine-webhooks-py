import os

from datetime import datetime
from pythonjsonlogger import jsonlogger

BROKER = os.environ.get('CELERY_BROKER')
API_KEY = os.environ.get('API_KEY')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')


class JSONFormatter(jsonlogger.JsonFormatter):
    """
    Class to add custom JSON fields to our logger.
    Presently just adds a timestamp if one isn't present and the log level.
    INFO: https://github.com/madzak/python-json-logger#customizing-fields
    """

    def add_fields(self, log_record, record, message_dict):
        super(JSONFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


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
            'class': 'microenginewebhookspy.settings.JSONFormatter',
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
