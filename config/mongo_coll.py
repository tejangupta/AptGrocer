from .mongo_conn import connect_db


# Listing collections here:
def get_collection(collection):
    db = connect_db()
    return db[collection]


# Listing collections here:
contacts = get_collection('contacts')
credentials = get_collection('credentials')
products = get_collection('products')
subscriptions = get_collection('subscriptions')
orderTransaction = get_collection('orderTransaction')
walletTransaction = get_collection('walletTransaction')
users = get_collection('users')
