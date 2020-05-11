import csv
from datetime import datetime
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from order import Order
import logging
import pdb
import pickle
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Scheduler:

    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.sched = BackgroundScheduler()
        self.sched.start()
        self.connection = Order.get_connection()
        self.csv_hash = self.get_csv_hash()

    def run_orders(self, *orders):
        for order in orders:
            try:
                response = order.run_commit(self.connection)
            except Exception as ex:
                logger.error(ex)

    def add_schedule(self, orders_dic):
        for timestamp, orders in orders_dic.items():
            self.sched.add_job(self.run_orders, trigger='date',
                               run_date=timestamp, args=orders)

    def stop_schedule(self):
        # Not strictly necessary if daemonic mode is enabled but
        # should be done if possible
        self.sched.shutdown()

    def get_order_from_csv_line(self, line):
        order_dic = {}
        order_dic['timestamp'] = line[0]
        order_dic['amount'] = float(line[1])
        order_dic['asset'] = line[2]
        order_dic['action'] = line[3]
        order_dic['duration'] = int(line[4])
        order_dic['gale_value'] = line[5]
        order = Order.from_dict(order_dic)
        return order

    def schedule_csv(self):
        orders = []
        orders_dic = {}
        with open(self.csv_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for n, line in enumerate(csv_reader):
                logger.info(f'Creating order from csv item {n}')
                order = self.get_order_from_csv_line(line)
                if orders_dic.get(order.timestamp):
                    orders_dic[order.timestamp].append(order)
                else:
                    orders_dic[order.timestamp] = [order]
                logger.info(f'Scheduling line {line}')

            self.add_schedule(orders_dic)

    def get_csv_hash(self):
        with open(self.csv_file, 'rb') as csv_file:
            checksum = hashlib.sha1(csv_file.read()).hexdigest()
        return checksum


if __name__ == '__main__':
    import os
    FOLDER = os.path.dirname(os.path.abspath(__file__))
    file = os.path.join(FOLDER, 'data.csv')
    sc = Scheduler(file)
    file_hash = sc.get_csv_hash()
    sc.schedule_csv()
    while True:
        if sc.get_csv_hash() != sc.csv_hash:
            sc.csv_hash = sc.get_csv_hash()
            logger.info('CSV file has changed @{datetime.now()} - hash{sc.csv_hash}!')
            sc.schedule_csv()
        # time.sleep(20)
        # print(f'Waiting {datetime.now()}')
