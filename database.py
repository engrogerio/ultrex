import apscheduler.jobstores.mongodb
from pymongo import MongoClient

def save(a_dict):
    with MongoClient("mongodb+srv://ultrex:ultrex@cluster0-z6gfh.mongodb.net/test?retryWrites=true&w=majority") as client:
        _db = client.get_database('ultrex')
        records = _db.ultrex  
        records.insert_one(a_dict)

def get_object_by_id(id):
    obj = ''
    with MongoClient("mongodb+srv://ultrex:ultrex@cluster0-z6gfh.mongodb.net/test?retryWrites=true&w=majority") as client:
        _db = client.get_database('ultrex')
        records = _db.ultrex
        obj = records.find_one({'_id': id})  
    return obj