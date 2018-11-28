import requests

def broadcast(type, nodes, query, data):
    for node in nodes:
        if data:
            response = requests.post('http://{}/broadcast/{}'.format(node, type), data)
        else:
            response = requests.get('http://{}/broadcast/{}'.format(node, type))

def broadcast_latest(data, nodes, post):
    broadcast('blockchain', data, nodes, post)

def broadcast_transaction_pool(transaction_pool, nodes, post):
    broadcast('transaction_pool', transaction_pool, nodes, post)
