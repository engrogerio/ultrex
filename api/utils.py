from iqoptionapi.stable_api import IQ_Option
import os
import sys
import logging
import time

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OptionApi:

    MODE = 'PRACTICE' # TODO: Where to set PRACTICE / REAL?

    def get_connection(self):
        user = os.environ.get('IQOPTIONAPI_USER', None)
        password = os.environ.get('IQOPTIONAPI_PASS', None)
        if not user:
            sys.exit("Missing environment variables IQOPTIONAPI_USER or IQOPTIONAPI_PASS !")

        connection = IQ_Option(user, password)
        check, reason = connection.connect()
        connection.change_balance(self.MODE)
        return connection



