#!/bin/env python

from flask import Flask, jsonify, request

# Instantiate the Node
from QuantumBlockChain import QuantumBlockChain
from POWBlockChain import POWBlockChain

app = Flask(__name__)


# Instantiate the Blockchain
blockchain = None


@app.route('/mine', methods=['GET'])
def do_mine():
    return blockchain.mine()

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
    else:
        blockchain = POWBlockChain()
    if args.db:
        print("DB: " + dbfile)
        blockchain.init_db(dbfile)
    app.run(host='0.0.0.0', port=port, threaded=True)
