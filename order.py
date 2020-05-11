import pdb
import threading
import logging
import database
from datetime import datetime
from api.utils import OptionApi
from threading import Thread


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        return OptionApi().get_connection()

    @classmethod
    def from_dict(cls, adict):
        timestamp = adict['timestamp']
        asset = adict['asset']
        amount = adict['amount']
        action = adict['action']
        duration = adict['duration']
        gale_value = adict['gale_value']
        return Order(timestamp, asset, amount, action,
                     duration, gale_value)

    def set_order_response(self, connection):
        response = connection.get_async_order(self.id).get('position-changed').get('msg')
        self.asset = response.get('raw_event').get('active')
        self.amount = response.get('raw_event').get('amount')
        self.action = response.get('raw_event').get('direction')
        self.duration = response.get('close_time') - response.get('open_time')
        # self.id = response.get('external_id')
        self.status = response.get('status')
        self.open_time = str(datetime.fromtimestamp(int(response.get('open_time'))/1000))
        self.close_time = str(datetime.fromtimestamp(int(response.get('close_time'))/1000))
        self.open_quote = response.get('open_quote')
        self.close_quote = response.get('close_quote')
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

    def commit(self, connection):
        """
        Commit the order and wait for a response.
        Also, save the response data.
        This method will run on a new thread.
        Args:
            asset: Name of the asset for the order_data
            amount: Value in BRL for the order_data
            action: call or put
            duration: Minutes before closing the order_data.

        Return:
            API Response

        Raise:
            None

        """

        logger.info(f"ordering: trade {self.asset} - {self.amount} - {self.action} - {self.duration}")

        success = False
        id = 0
        # Try binary first
        logger.info(f'Trying order {self.action} {self.asset} in binary...{threading.currentThread().getName()}')
        try:
            success, id = connection.buy(self.amount, self.asset, self.action.lower(), self.duration)
        except Exception as ex:
            logger.error(ex)

        if success:
            logger.info(f'Binary order_data was placed with id {id}.')

        else:
            logger.info(f'Trying order {self.action} {self.asset} in digital {threading.currentThread().getName()}...')
            try:
                success, id = connection.buy_digital_spot(self.asset, self.amount, self.action.lower(), self.duration)
            except Exception as ex:
                logger.error(ex)
            if success:
                logger.info(f'Digital order was placed with id {id}.')

            else:
                logger.warning(f'The asset {self.asset} could not be ordered today due to {id["message"]}!')

        if success:
            # waits for API get ready
            logger.info(f'Waiting for response for id {id} on thread {threading.currentThread().getName()}!')
            while not connection.get_async_order(id):
                pass  # do nothing

            logger.info(f'Waiting for closed order id {id} on thread {threading.currentThread().getName()}!')
            state = 'open'
            while state != 'closed':
                try:
                    state = connection.get_async_order(id).get('position-changed', '').get('msg', '').get('status', '')
                except Exception as ex:
                    state = 'open'

            self.id = id
            self.set_order_response(connection)
            logger.info(f'Order {id} placed on thread {threading.currentThread().getName()}!', self.to_dict())
            response = {'message': self.to_dict()}
            # save closed order data
            database.save(connection.get_async_order(id)) #self.to_dict())
        else:
            response = id
        return response

    def run_commit(self, connection):
        t = Thread(target=self.commit, args=(connection,))
        t.start()
