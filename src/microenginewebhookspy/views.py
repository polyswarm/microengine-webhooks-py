import dataclasses
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
            logger.debug('Kicking off new scan with %s', bounty)
            expiration = dateutil.parser.parse(bounty.expiration)
            handle_bounty.apply_async((dataclasses.asdict(bounty),), expires=expiration)
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
