import dataclasses
import datetime
import dateutil.parser
import logging

from flask import request, jsonify, Blueprint

from microenginewebhookspy.models import Bounty


POLYSWARM_EVENT_NAME_HEADER = 'X-POLYSWARM-EVENT'

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)


@api.route('/', methods=['POST'])
def bounty_request_handler():
    from microenginewebhookspy.tasks import handle_bounty
    event_name = request.headers.get(POLYSWARM_EVENT_NAME_HEADER, '').lower()

    if event_name == 'bounty':
        try:
            body = request.get_json()
            bounty = Bounty(**body)
            expiration = dateutil.parser.parse(bounty.expiration)
            delta = expiration - datetime.datetime.now(datetime.UTC)
            soft_limit = int(delta.total_seconds())
            logger.debug('Processing new bounty %s with %s seconds until expiration', bounty, soft_limit)
            handle_bounty.apply_async((dataclasses.asdict(bounty),), soft_time_limit=soft_limit, expires=expiration)
            return jsonify({'status': 'ACCEPTED'}), 202
        except (TypeError, KeyError, ValueError) as err:
            logger.exception('Bad Request')
            return jsonify({'bounty': 'Invalid bounty request'}), 400
    if event_name == 'ping':
        return jsonify({'status': 'OK'}), 200
    else:
        return jsonify({'X-POLYSWARM-EVENT': f'Given event not supported'}), 400


@api.route('/', methods=['GET'])
def liveness_request_handler():
    return jsonify({'status': 'OK'}), 200
