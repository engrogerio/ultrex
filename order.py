# python imports
import pdb
import threading
import logging
import time
from datetime import datetime
from threading import Thread

# external libraries
from api.utils import iqoption_connection

# local imports
import database

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
datefmt='%Y-%m-%d:%H:%M:%S',
level=logging.ERROR)
logger = logging.getLogger(__name__)


class Order:

    def __init__(self, timestamp: str, asset: str, amount: float,
                 action: str, duration: int, gale_value: int,
                 id='', status='open', open_time='', close_time='',
                 open_quote=0.0, close_quote=0.0, result=''):
        self.timestamp = timestamp
        self.asset = asset
        self.amount = amount
        self.action = action
        self.duration = duration
        self.gale_value = gale_value
        self.id = id
        self.status = status
        self.open_time = open_time
        self.close_time = close_time
        self.open_quote = open_quote
        self.close_quote = close_quote
        self.result = result

    def to_dict(self):
        return {
                "timestamp": self.timestamp,
                "asset": self.asset,
                "amount": self.amount,
                "action": self.action,
                "duration": self.duration,
                "gale_value": self.gale_value,
                "id": self.id,
                "status": self.status,
                "open_time": self.open_time,
                "close_time": self.close_time,
                "open_quote": self.open_quote,
                "close_quote": self.close_quote,
                "result": self.result
                }

    @classmethod
    def get_connection(cls):
        return iqoption_connection()

    @classmethod
    def from_dict(cls, adict):
        timestamp = adict['timestamp']
        asset = adict['asset']
        amount = float(adict['amount'])
        action = adict['action']
        duration = int(adict['duration'])
        gale_value = adict['gale_value']
        return Order(timestamp, asset, amount, action,
                     duration, gale_value)

    def set_order_response(self, response_msg):
        self.asset = response_msg.get('raw_event').get('active')
        self.amount = response_msg.get('raw_event').get('amount')
        self.action = response_msg.get('raw_event').get('direction')
        self.duration = response_msg.get('close_time') - response_msg.get('open_time')
        self.status = response_msg.get('status')
        self.open_time = str(datetime.fromtimestamp(int(response_msg.get('open_time'))/1000))
        self.close_time = str(datetime.fromtimestamp(int(response_msg.get('close_time'))/1000))
        self.open_quote = response_msg.get('open_quote')
        self.close_quote = response_msg.get('close_quote')
        if self.action == 'put':
            self.result = 'win' if self.close_quote > self.open_quote else 'loose'
        else:
            self.result = 'win' if self.close_quote < self.open_quote else 'loose'

    @classmethod
    def get_available_assets(cls, connection):
        availables = {}
        opn = connection.get_all_open_time()
        binary = opn.get('binary')
        digital = opn.get('digital')
        availables['binary'] = [asset for asset, value in binary.items() if value['open']]
        availables['digital'] = [asset for asset, value in digital.items() if value['open']]
        return availables

    def buy_binary(self, connection):
        try:
            success, iq_id = connection.buy(
                self.amount, self.asset, self.action.lower(), self.duration)
            if success:
                logger.info(f'binary = {iq_id} - order placed')
            return {"success": success, "id": iq_id}

        except Exception as ex:
            logger.error(ex)
            return {"success": False, "error": ex}

    def buy_digital(self, connection):
        try:
            success, iq_id = connection.buy_digital_spot(
                self.asset, self.amount, self.action.lower(), self.duration)
            if success:
                logger.info(f'digital ={iq_id} - order placed')
            return {"success": success, "id": iq_id}

        except Exception as ex:
            logger.error(ex)
            return {"success": False, "error": ex}

    def get_async_order_response(self, connection, iq_id):
        logger.debug(connection.get_async_order(iq_id))
        return connection.get_async_order(iq_id)

    def commit(self, connection):

        # Try binary first
        iq_result = {}

        try:
            iq_result = self.buy_binary(connection)

        except Exception as ex:
            logger.error(ex)

        if not iq_result.get('success', False):
            # binary did not go through. Trying digital
            try:
                iq_result = self.buy_digital(connection)

            except Exception as ex:
                logger.error(ex)

        if iq_result.get('success', False):
            # if any succeed, waits for API get ready.
            print(f'waiting thread {threading.currentThread().getName()}')
            while not self.get_async_order_response(connection, iq_result['id']):
                time.sleep(10)
                pass

            # waits for the order to close.
            logger.debug(f'started thread {threading.currentThread().getName()}')
            state = 'open'
            while state != 'closed':
                try:
                    response = self.get_async_order_response(connection, iq_result['id']).get('position-changed')
                    state = response.get('msg').get('status')
                except Exception as ex:
                    log.error(f'raised exception {ex}')
                    state = 'open'
            logger.debut(f'ended order thread {threading.currentThread().getName()}')

            # saves data back to the self
            self.set_order_response(response.get('msg'))

            response = {'message': self.to_dict()}

            # save closed order data
            database.save(self.to_dict()) #connection.get_async_order(id))
        else:
            response = iq_result.get('id')
        return response

    def run_commit(self, connection):
        t = Thread(target=self.commit, args=(connection,))
        t.start()

