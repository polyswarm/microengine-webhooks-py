import os

BROKER = os.environ.get('CELERY_BROKER_URL')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
