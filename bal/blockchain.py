#!/usr/bin/env python

from flask import Flask, jsonify, request

# Instantiate the peer
from POWBlockchain import POWBlockchain
from POSBlockchain import POSBlockchain

from POWBlockchainSimulation import POWBlockchainSimulation
from POSBlockchainSimulation import POSBlockchainSimulation

from Transaction import new_transaction
from TransactionPool import TransactionPool
from Wallet import init_wallet, get_public_from_wallet, get_private_from_wallet, create_transaction

import threading
import yaml
import json
import traceback
app = Flask(__name__)


# Instantiate the Blockchain
blockchain = None
loop_started = False

@app.route('/transactions/unspenttxouts', methods=['GET'])
def do_unspent_tx_outputs():
    return jsonify(blockchain.unspent_tx_outs), 200

@app.route('/transactions/unspenttxouts/my', methods=['GET'])
def do_my_unspent_tx_outs():
    return jsonify(blockchain.get_my_unspent_transaction_outputs()), 200

@app.route('/address/my', methods=['GET'])
def do_address():
    address = get_public_from_wallet()
    return jsonify({'address': address}), 200

@app.route('/balance/my', methods=['GET'])
def do_get_my_balance():
    balance = blockchain.get_my_account_balance()
    return jsonify({'balance': balance}), 200

@app.route('/balance/<address>', methods=['GET'])
def do_get_balance(address):
    balance = blockchain.get_account_balance(address)
    return jsonify({'balance': balance}), 200

@app.route('/transactions/pool', methods=['GET'])
def do_get_transaction_pool():
    return jsonify(blockchain.transaction_pool.get_transaction_pool()), 200

@app.route('/block/generate', methods=['GET'])
def do_generate_block():
    new_block = blockchain.generate_next_block()
    if new_block:
        return jsonify(new_block), 200
    else:
        return 'Could not generate new block', 400

@app.route('/block/generate/loop/start', methods=['GET'])
def do_generate_loop_start():
    global loop_started
    try:
        if loop_started:
            return "Loop has already started.", 200
        loop_started = True
        threading.Thread(
                target = do_generate_loop_helper,
        ).start()
        return "Started Generation Loop (Asynchronous)", 200
    except Exception as e:
        traceback.print_exc()
        return jsonify(str(e)), 500

@app.route('/block/generate/loop/stop', methods=['GET'])
def do_generate_loop_stop():
    global loop_started
    try:
        loop_started = False
        return "Stopped Generation Loop", 200
    except Exception as e:
        traceback.print_exc()
        return jsonify(str(e)), 500

def do_generate_loop_helper():
    global loop_started
    try:
        while(loop_started):
            new_block = blockchain.generate_next_block()
    except Exception:
        traceback.print_exc()

@app.route('/block/latest', methods=['GET'])
def do_latest_block():
    return jsonify(blockchain.get_latest_block()), 200

@app.route('/block/<int:index>', methods=['GET'])
def do_block_index(index):
    return jsonify(blockchain.get_blockchain()[index]), 200

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
        traceback.print_exc()
        tx = str(e)
        return jsonify(tx), 200

    return jsonify(tx), 200

@app.route('/transactions/has_amount/<int:amount>', methods=['GET'])
def do_has_amount_for_transaction(amount):
    try:
        create_transaction(get_public_from_wallet(), amount, get_private_from_wallet(), blockchain.get_unspent_tx_outs(), blockchain.transaction_pool.get_transaction_pool())
        return jsonify(True), 200
    except Exception as e:
        traceback.print_exc()
        tx = str(e)
        return jsonify(False), 200

@app.route('/chain', methods=['GET'])
def do_full_chain():
    return jsonify(blockchain.full_chain()), 200

@app.route('/chain/length', methods=['GET'])
def do_chain_length():
    return jsonify(blockchain.full_chain()['length']), 200

@app.route('/peers', methods=['GET'])
def do_get_peers():
    return jsonify(blockchain.p2p.get_peers()), 200

@app.route('/peers/register', methods=['POST'])
def do_register_peers():
    values = yaml.safe_load(json.dumps(request.get_json()))['peer']
    if not values:
        return 'Missing values', 200
    return jsonify(blockchain.p2p.add_peer(values)), 200

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-s', '--socket', default=6001, type=int, help='p2p port to listen on')
    parser.add_argument('-db', '--database', default='', help='db file')
    parser.add_argument('-v', '--variant', default='pow', help='variant of blockchain "pow" or "pos"')
    parser.add_argument('-d', '--difficulty', default=4, type=int, help='initial difficulty')
    parser.add_argument('-k', '--keystore', default='/tmp/private_key.pem', help='where the keystore located. default: private_key.pem')
    parser.add_argument('-sp', '--simulationpath', default='', help='specifies if it is a simulation run and where simulation logs will be kept.')
    parser.add_argument('-n', '--name', default='bc', help='specifies blockchain node name(mostly for simulations)')

    args = parser.parse_args()
    port = args.port
    dbfile = args.database
    p2p_port = args.socket
    initial_difficulty = args.difficulty
    simulation_path = args.simulationpath
    if simulation_path != '':
        if args.variant.find('pos') == 0:
            blockchain = POSBlockchainSimulation(p2p_port, initial_difficulty, simulation_path, args.name)
        else:
            blockchain = POWBlockchainSimulation(p2p_port, initial_difficulty, simulation_path, args.name)
    else:
        if args.variant.find('pos') == 0:
            blockchain = POSBlockchain(p2p_port, initial_difficulty)
        else:
            blockchain = POWBlockchain(p2p_port, initial_difficulty)

    if dbfile:
        print("DB: " + dbfile)
        blockchain.init_db(dbfile)
    init_wallet(args.keystore)
    threading.Thread(
        target = blockchain.p2p.start,
        args = ()
    ).start()
    app.run(host='0.0.0.0', port=port, threaded=True)
