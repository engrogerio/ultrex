import os
import sys
import hashlib
import csv
    
class Csv:
    
    def __init__(self):
        self.csv_file = self.get_file_path()
        
    def get_csv_hash(self):
        with open(self.csv_file, 'rb') as csv_file:
            checksum = hashlib.sha1(csv_file.read()).hexdigest()
        return checksum
    
    def get_file_path(self):
        FOLDER = os.getcwd()
        return os.path.join(FOLDER, 'data.csv')
    
    def to_dict(self):
        """
        Get a dictionary from csv data.
        """
        adict = {}
        with open(self.csv_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for n, line in enumerate(csv_reader):
                adict[n + 1] = {
                                    "timestamp": line[0],
                                    "amount": line[1],
                                    "asset": line[2],
                                    "action": line[3],
                                    "duration": line[4],
                                    "gale_value": line[5]
                                }
                
        return adict    