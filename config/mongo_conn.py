from pymongo import MongoClient
from dotenv import load_dotenv
import os


# Function to establish a connection to the database
def connect_db():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(base_dir, 'mongodb.env'))

    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['db-grocery']
    return db


if __name__ == '__main__':
    connect_db()
