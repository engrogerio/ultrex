# python imports
from datetime import datetime
import time
import os
import pdb
import pickle
import logging

# external imports
from apscheduler.schedulers.background import BackgroundScheduler

# project imports
from order import Order
from ultrex_csv import Csv


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
datefmt='%Y-%m-%d:%H:%M:%S',
level=logging.ERROR)
logger = logging.getLogger(__name__)

class Scheduler:

    def __init__(self):
        # A Scheduler just needs a csv file to start
        self.schedule = BackgroundScheduler()
        self.iqoption_connection = Order.get_connection()
        self.start()

    def start(self):
        self.schedule.start()

    def run_orders(self, *orders):
        for order in orders:
            try:
                response = order.run_commit(self.iqoption_connection)
            except Exception as ex:
                logger.error(ex)

    def add_schedule(self, order):
        self.schedule.add_job(self.run_orders, trigger='date',
                            run_date=order.timestamp, args=[order])

    def stop_schedule(self):
        # Not strictly necessary if daemonic mode is enabled but
        # should be done if possible
        self.schedule.shutdown()

    def schedule_list_content(self, lines_list):

        """
        Read a list and send the data to
        be run on a schedule.
        """
        print('*********', lines_list)
        for key, line in enumerate(lines_list):
            order = Order.from_dict(line)
            logger.info(f"Scheduling item {key} - {line['asset']}")
            self.add_schedule(order)

    def schedule_csv_content(self, csv_file):
        """
        Read a csv file and send the data to
        be run on a schedule.
        """
        self.schedule_list_content(csv_file.to_dict().items())

def main_test():
    from datetime import datetime
    sc = Scheduler()
    schedule = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'EURUSD-OTC','CALL',1,1]
    sc.schedule_list_content(schedule)

def main_prod():

    csv_file = Csv()
    sc = Scheduler()
    file_hash = csv_file.get_csv_hash()
    sc.schedule_csv_content(csv_file)

    while True:
        # check if the file has changed
        if csv_file.get_csv_hash() != file_hash:
            file_hash = csv_file.get_csv_hash()
            logger.info(f'CSV file has changed @{datetime.now()} - hash: {file_hash}!')
            sc.schedule_csv_content(csv_file)
        # time.sleep(10)

if __name__ == "__main__":
    main_prod()
