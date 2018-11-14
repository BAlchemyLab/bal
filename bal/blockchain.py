#!/bin/env python

from flask import Flask, jsonify, request

# Instantiate the Node
from QuantumBlockChain import QuantumBlockChain
from POWBlockChain import POWBlockChain
from POSBlockChain import POSBlockChain

from Transaction import Transaction
from TransactionPool import get_transaction_pool
from p2p import broadcast_latest, broadcast_transaction_pool
from Wallet import init_wallet

app = Flask(__name__)


# Instantiate the Blockchain
blockchain = None

@app.route('/transcations/unspenttxouts', methods=['GET'])
def get_unspent_tx_outputs():
    return jsonify(blockchain.unspent_tx_outs), 200

@app.route('/transcations/unspenttxouts/my', methods=['GET'])
def my_unspent_tx_outs():
    return jsonify(blockchain.get_my_unspent_transaction_outputs()), 200

@app.route('/balance', methods=['GET'])
def r_get_balance():
    balance = blockchain.get_account_balance()
    return jsonify({'balance': balance}), 200

@app.route('/transactionPool', methods=['GET'])
def r_get_transaction_pool():
    return jsonify(get_transaction_pool()), 200

@app.route('/mine', methods=['GET'])
def do_mine():
    return blockchain.mine()

@app.route('/block/new', methods=['POST'])
def new_block():
    values = request.get_json()
    return blockchain.new_block(values['index'], values['timestamp'],
                                values['previous_hash'], values['transactions'],
                                values['difficulty'],
                                values['staker_balance'], values['staker_address'])

@app.route('/transactions/new', methods=['POST'])
def do_new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'],
                                       values['recipient'],
                                       values['amount'])

    response = {'message': 'Transaction will be added to Block {}'.format(index)}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def do_full_chain():
    return jsonify(blockchain.full_chain()), 200

@app.route('/nodes', methods=['GET'])
def do_get_nodes():
    return blockchain.get_nodes()

@app.route('/nodes', methods=['DELETE'])
def do_remove_nodes():
    blockchain.remove_nodes()
    response = {
        'message': 'Nodes removed',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response)

@app.route('/nodes/register', methods=['POST'])
def do_register_nodes():
    values = request.get_json()

    return blockchain.register_nodes(values)

@app.route('/nodes/resolve', methods=['GET'])
def do_consensus():
    return blockchain.consensus()

@app.route('/broadcast/blockchain', methods=['POST'])
def get_broadcast_latest():
    values = request.get_json()
    if not values:
        print('invalid blocks received: %s', json.dumps(values))
        return

    handle_blockchain_response(received_blocks)

@app.route('/broadcast/transaction_pool', methods=['POST'])
def get_broadcast_transaction_pool():
    received_transactions = request.get_json()
    if not received_transactions:
        print('invalid transaction received: %s', json.dumps(value))
        return

    for transaction in received_transactions:
        try:
            blockchain.handle_received_transaction(transaction)
            broadcast_transaction_pool()
        except:
            print(e.message)

@app.route('/broadcast/blockchain', methods=['GET'])
def get_all_blockchain_broadcast():
    return jsonify(blockchain.full_chain()), 200

def broadcast(type, data):
    for node in blockchain.nodes:
        if data:
            response = requests.post('http://{}/broadcast/{}'.format(node, type), data)
        else:
            response = requests.get('http://{}/broadcast/{}'.format(node, type))

def handle_blockchain_response(received_blocks):
    if len(receivedBlocks == 0):
        print('received block chain size of 0')
        return

    latest_block_received = received_blocks[-1]
    if not blockchain.is_valid_block_structure(latest_block_received):
        print('block structuture not valid')
        return

    latest_block_held = blockchain.get_latest_block()
    if latest_block_received['index'] > latest_block_held['index']:
        if latest_block_held['hash'] == latest_block_received['previous_hash']:
            if add_block_to_chain(latest_block_received):
                broadcast_latest([blockchain.get_latest_block()])
            elif len(received_blocks) == 1:
                print('We have to query the chain from our peer')
                broadcast('blockchain')
        else:
            print('Received blockchain is longer than current blockchain')
            block_chain.replace_chain(received_blocks)
    else:
        print('received blockchain is not longer than received blockchain. Do nothing')

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-d', '--db', default='', help='db file')
    parser.add_argument('-v', '--variant', default='pow', help='variant of blockchain "pow[:initial_difficulty]" or "quant"')
    args = parser.parse_args()
    port = args.port
    dbfile = args.db
    if args.variant.find('pow') == 0:
        pow = args.variant.split(':')
        if len(pow) == 2:
            blockchain = POWBlockChain(initial_difficulty=int(pow[1]))
        else:
            blockchain = POWBlockChain()
    elif args.variant == 'quant':
        blockchain = QuantumBlockChain(app)
    elif args.variant == 'pos':
        blockchain = POSBlockChain()
        init_wallet()
    else:
        blockchain = POWBlockChain()
    if args.db:
        print("DB: " + dbfile)
        blockchain.init_db(dbfile)
    app.run(host='0.0.0.0', port=port, threaded=True)
