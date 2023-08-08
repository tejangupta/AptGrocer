from pymongo import MongoClient
import os


# Function to establish a connection to the database
def connect_db():
    client = MongoClient(os.environ.get('MONGODB_URI'))
    db = client['db-grocery']
    return db


if __name__ == '__main__':
    connect_db()
