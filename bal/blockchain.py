#!/bin/env python

from flask import Flask, jsonify, request

# Instantiate the peer
from QuantumBlockChain import QuantumBlockChain
from POWBlockChain import POWBlockChain
from POSBlockChain import POSBlockChain

from Transaction import new_transaction
from TransactionPool import TransactionPool
from Wallet import init_wallet, get_public_from_wallet

import threading
import yaml
import json
app = Flask(__name__)


# Instantiate the Blockchain
blockchain = None

@app.route('/transactions/unspenttxouts', methods=['GET'])
def get_unspent_tx_outputs():
    return jsonify(blockchain.unspent_tx_outs), 200

@app.route('/transactions/unspenttxouts/my', methods=['GET'])
def my_unspent_tx_outs():
    return jsonify(blockchain.get_my_unspent_transaction_outputs()), 200

@app.route('/address/my', methods=['GET'])
def r_address():
    address = get_public_from_wallet()
    return jsonify({'address': address}), 200

@app.route('/balance/my', methods=['GET'])
def r_get_my_balance():
    balance = blockchain.get_my_account_balance()
    return jsonify({'balance': balance}), 200

@app.route('/balance/<address>', methods=['GET'])
def r_get_balance(address):
    balance = blockchain.get_account_balance(address)
    return jsonify({'balance': balance}), 200

@app.route('/transactions/pool', methods=['GET'])
def r_get_transaction_pool():
    return jsonify(blockchain.transaction_pool.get_transaction_pool()), 200

@app.route('/block/generate', methods=['GET'])
def r_generate_block():
    new_block = blockchain.generate_next_block()
    if new_block:
        return jsonify(new_block), 200
    else:
        return 'Could not generate new block', 400

@app.route('/block/new', methods=['POST'])
def new_block():
    values = yaml.safe_load(json.dumps(request.get_json()))
    return blockchain.new_block(values['index'], values['timestamp'],
                                values['previous_hash'], values['transactions'],
                                values['difficulty'],
                                values['staker_balance'], values['staker_address'])

@app.route('/transactions/send', methods=['POST'])
def do_new_transaction():
    values = yaml.safe_load(json.dumps(request.get_json()))

    # Check that the required fields are in the POST'ed data
    required = ['recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new new_transaction
    try:
        tx = blockchain.send_transaction(values['recipient'], values['amount'])
    except Exception as e:
        tx = str(e)

    return jsonify(tx), 201


@app.route('/chain', methods=['GET'])
def do_full_chain():
    return jsonify(blockchain.full_chain()), 200

@app.route('/peers', methods=['GET'])
def do_get_peers():
    return jsonify(blockchain.p2p.get_peers()), 200

@app.route('/peers/register', methods=['POST'])
def do_register_peers():
    values = yaml.safe_load(json.dumps(request.get_json()))['peer']
    if not values:
        return 'Missing values', 200
    return jsonify(blockchain.p2p.add_peer(values)), 200

#----------------------------------------------------------
#POW
@app.route('/peers/resolve', methods=['GET'])
def do_consensus():
    return blockchain.consensus()

@app.route('/mine', methods=['GET'])
def do_mine():
    return blockchain.mine()

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-s', '--socket', default=6001, type=int, help='p2p port to listen on')
    parser.add_argument('-d', '--db', default='', help='db file')
    parser.add_argument('-v', '--variant', default='pow', help='variant of blockchain "pow[:initial_difficulty]" or "quant"')
    parser.add_argument('-k', '--keystore', default='/tmp/private_key.pem', help='where the keystore located. default: private_key.pem')

    args = parser.parse_args()
    port = args.port
    dbfile = args.db
    p2p_port = args.socket
    if args.variant.find('pow') == 0:
        pow = args.variant.split(':')
        if len(pow) == 2:
            blockchain = POWBlockChain(initial_difficulty=int(pow[1]))
        else:
            blockchain = POWBlockChain()
    elif args.variant == 'quant':
        blockchain = QuantumBlockChain(app)
    elif args.variant == 'pos':
        blockchain = POSBlockChain(p2p_port)
        init_wallet(args.keystore)
        threading.Thread(
            target = blockchain.p2p.start,
            args = ()
        ).start()
    else:
        blockchain = POWBlockChain()
    if args.db:
        print("DB: " + dbfile)
        blockchain.init_db(dbfile)
    app.run(host='0.0.0.0', port=port, threaded=True)
