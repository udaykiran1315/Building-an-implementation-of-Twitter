from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["A2-3211471"]

users = db["users"]
tweets = db["tweets"]