#!/bin/env python

from uuid import uuid4

import requests
from flask import Flask, jsonify, request

# Instantiate the Node
from QuantumBlockChain import QuantumBlockChain
from POWBlockChain import POWBlockChain

app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = 0


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)

    blockchain.save_db()

    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': 'Transaction will be added to Block {}'.format(index)}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify(blockchain.full_chain()), 200

@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'message': 'Nodes',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response)

@app.route('/nodes', methods=['DELETE'])
def remove_nodes():
    blockchain.remove_nodes()
    response = {
        'message': 'Nodes removed',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response)

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        blockchain.save_db()
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-k', '--kwport', default=55554, type=int, help='port keyworker to listen on')
    parser.add_argument('-i', '--ip', default='127.0.0.1', help='ip keyworker to listen on')
    parser.add_argument('-d', '--db', default='', help='db file')
    parser.add_argument('-v', '--variant', default='pow', help='variant of blockchain "pow[:difficulty]" or "quant"')
    args = parser.parse_args()
    port = args.port
    kwport = args.kwport
    kwip = args.ip
    dbfile = args.db
    if args.variant.find('pow') == 0:
        pow = args.variant.split(':')
        if len(pow) == 2:
            blockchain = POWBlockChain(difficulty=int(pow[1]))
        else:
            blockchain = POWBlockChain()
    elif args.variant == 'quant':
        blockchain = QuantumBlockChain(kwip, kwport)
    else:
        blockchain = POWBlockChain()
    if args.db:
        blockchain.init_db(dbfile)
    app.run(host='0.0.0.0', port=port)
