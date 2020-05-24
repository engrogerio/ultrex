from iqoptionapi.stable_api import IQ_Option
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def iqoption_connection():
    MODE = 'PRACTICE'  # TODO: Where to set PRACTICE / REAL?
    user = os.environ.get('IQOPTIONAPI_USER', None)
    password = os.environ.get('IQOPTIONAPI_PASS', None)
    if not user:
        sys.exit("Missing environment variables IQOPTIONAPI_USER or IQOPTIONAPI_PASS !")
    connection = IQ_Option(user, password)
    check, reason = connection.connect()
    if not check:
        raise Exception(reason)
    connection.change_balance(MODE)
    return connection
