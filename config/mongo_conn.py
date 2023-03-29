from pymongo import MongoClient

# Database Configuration
settings = {
    'mongoConfig': {
        # Fill in the details for the MongoDB URI
        'serverUrl': 'mongodb+srv://username:password@clustername.mongodb.net/databaseName?retryWrites=true&w=majority',
        'database': 'db-grocery'
    }
}


# Function to establish a connection to the database
def connect_db():
    client = MongoClient(settings['mongoConfig']['serverUrl'])
    db = client[settings['mongoConfig']['database']]
    return db
