import requests
from TransactionPool import get_transaction_pool

def broadcast(type, data):
    for node in blockchain.nodes:
        if data:
            response = requests.post('http://{}/broadcast/{}'.format(node, type), data)
        else:
            response = requests.get('http://{}/broadcast/{}'.format(node, type))

def broadcast_latest(data):
    broadcast('blockchain', data)

def broadcast_transaction_pool(data):
    broadcast('transaction_pool', get_transaction_pool())
