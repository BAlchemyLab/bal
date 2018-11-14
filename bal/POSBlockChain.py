# Python 3 -> 2 compatibility
# Python 3 -> 2 compatibility
try:  # Python 3
    from urllib.parse import urlparse
except:
    from urlparse import urlparse

from uuid import uuid4
import hashlib
import json
from time import time
import abc
import shelve
from flask import jsonify
import functools

from builtins import super
import requests
import copy
from functional import seq
import numbers
from attrdict import AttrDict

import hashlib

from p2p import broadcast_latest, broadcast_transaction_pool
from Transaction import new_coinbase_transaction, is_valid_address, process_transactions, Transaction, UnspentTxOut
from TransactionPool import add_to_transaction_pool, get_transaction_pool, update_transaction_pool
from Wallet import create_transaction, find_unspent_tx_outs, get_balance, get_private_from_wallet, get_public_from_wallet

VALIDATING_WITHOUT_COIN = 100
DIFFICULTY_ADJUSTMENT_INTERVAL = 16 # block number
BLOCK_GENERATION_INTERVAL = 5 # in seconds
VALID_TIMESTAMP_INTERVAL = 60 # in seconds

class POSBlockChain:
    def __init__(self, initial_difficulty=4):
        self.current_transactions = []
        # Create the genesis block
        self.chain = [self.genesis_block()]
        self.nodes = set()
        self.db = None
        self.unspent_tx_outs = process_transactions(self.chain[0]['transactions'], [], 0)
        # Generate a globally unique address for this node
        self.node_identifier = str(uuid4()).replace('-', '')
        self.difficulty = initial_difficulty

    @property
    def unspent_tx_outs(self):
        return copy.deepcopy(self.__unspent_tx_outs)

    @unspent_tx_outs.setter
    def unspent_tx_outs(self, unspent_tx_outs):
        self.__unspent_tx_outs = unspent_tx_outs

    def get_latest_block(self):
        return self.chain[-1]

    def get_blockchain(self):
        return self.chain
        
    def get_unspent_tx_outs(self):
        self.unspent_tx_outs

    def genesis_transaction(self):
        return  AttrDict({
                    'tx_ins': [{'signature': '', 'tx_out_id': '', 'tx_out_index': 0}],
                    'tx_outs': [{
                        'address': '04bfcab8722991ae774db48f934ca79cfb7dd991229153b9f732ba5334aafcd8e7266e47076996b55a14bf9913ee3145ce0cfc1372ada8ada74bd287450313534a',
                        'amount': 50
                    }],
                    'id': 'e655f6a5f26dc9b4cac6e46f52336428287759cf81ef5ff10854f69d68f43fa3'
                })

    def genesis_block(self):
        return self.new_block(0, 1465154705, '', [self.genesis_transaction()], 0, 0, '04bfcab8722991ae774db48f934ca79cfb7dd991229153b9f732ba5334aafcd8e7266e47076996b55a14bf9913ee3145ce0cfc1372ada8ada74bd287450313534a')

    def get_difficulty(self, a_block_chain):
        latest_block = a_block_chain[-1]
        if latest_block['index'] % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and latest_block['index'] != 0:
            return self.get_adjusted_difficulty(latest_block, a_block_chain)
        else:
            return latest_block['difficulty']

    def get_adjusted_difficulty(self, latest_block, a_block_chain):
        prev_adjustment_block = a_block_chain[-1 * DIFFICULTY_ADJUSTMENT_INTERVAL]
        time_expected = BLOCK_GENERATION_INTERVAL * DIFFICULTY_ADJUSTMENT_INTERVAL
        time_taken = latest_block['timestamp'] - prev_adjustment_block['timestamp']
        if time_taken < time_expected / 2:
            return prev_adjustment_block['difficulty'] + 1
        elif time_taken > time_expected * 2:
            return prev_adjustment_block['difficulty'] - 1
        else:
            return prev_adjustment_block['difficulty']

    def is_valid_timestamp(block, previous_block):
        result = (previous_block['timestamp'] - VALID_TIMESTAMP_INTERVAL < block['timestamp']) and \
                    block['timestamp'] - VALID_TIMESTAMP_INTERVAL < time()
        return result

    def new_block(self, index, timestamp, previous_hash, transactions, difficulty, staker_balance, staker_address):
        """
        Create a new Block in the Blockchain
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = AttrDict({
            'index': index,
            'timestamp': timestamp,
            'previous_hash': previous_hash,
            'transactions': transactions,
            'difficulty': difficulty,
            'staker_balance': staker_balance,
            'staker_address': staker_address
        })

        block['hash'] = self.hash(block)
        return block

    def generate_raw_next_block(self, transactions):
        previous_block = get_latest_block()
        difficulty = get_difficulty(self.chain)
        next_index = previous_block['index'] + 1
        new_block = find_block(next_index, previous_block['hash'], transactions, difficulty)
        if add_block_to_chain(new_block):
            broadcast_latest()
            return new_block
        else:
            return None

    def get_my_unspent_transaction_outputs():
        return find_unspent_tx_outs(get_public_from_wallet(), self.unspent_tx_outs())

    def generate_next_block():
        coinbase_tx = new_coinbase_transaction(get_public_from_wallet(), get_latest_block()['index'] + 1)
        block_data = [coinbase_tx].merge(get_transaction_pool())
        return generate_raw_next_block(block_data)


    def generate_next_block_with_transaction(receiver_address, amount):
        if not is_valid_address(receiver_address):
            raise('invalid address')

        if not isinstance(amount, numbers.Number):
            raise('invalid amount')

        coinbase_tx = new_coinbase_transaction(get_public_from_wallet(), latest_block()['index'] + 1)
        tx = create_transaction(receiver_address, amount, get_private_from_wallet(), self.unspent_tx_outs(), get_transaction_pool())
        block_data = [coinbase_tx, tx]
        return generate_raw_next_block(block_data)

    def is_block_staking_valid(self, block):
        difficulty = block['difficulty'] + 1

        if block['index'] <= VALIDATING_WITHOUT_COIN:
            balance = block['staker_balance'] + 1

        balance_over_difficulty = (2**256) * balance/difficulty
        previous_hash = block['previous_hash']
        staker_address = block['staker_address']
        timestamp = block['timestamp']

        guess = '{}{}{}'.format(previous_hash, staker_address, timestamp).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        staking_hash_decimal = int(guess_hash, 16)
        difference = balance_over_difficulty - staking_hash_decimal

        return difference >= 0

    def find_block(self, index, previous_hash, transactions, difficulty):
        previous_time_stamp = 0
        while (True):
            timestamp = time()
            if previous_time_stamp != timestamp:
                temp_block = new_block(index, timestamp, previous_hash, transactions, difficulty, get_balance(), get_public_address())
                if is_block_staking_valid(temp_block):
                    return temp_block
                previous_time_stamp = timestamp

    def get_account_balance(self):
        return get_balance(get_public_from_wallet(), self.unspent_tx_outs())

    def send_transaction(address, amount):
        tx = create_transaction(address, amount, get_private_from_wallet(), self.unspent_tx_outs(), get_transaction_pool())
        add_to_transaction_pool(tx, self.unspent_tx_outs())
        broadcast_transaction_pool()
        return tx

    def is_valid_block_structure(block):
        return isinstance(block['index'], numbers.Number) and \
                 type(block['hash']) == str and \
                 type(block['previousHash']) == str and \
                 isinstance(block['timestamp'], numbers.Number) and \
                 type(block['transactions']) == dict and \
                 isinstance(block['difficulty'], numbers.Number) and \
                 isinstance(block['minterBalance'], number.Number) and \
                 type(block['minterAddress']) == str

    def has_valid_hash(block):
        if not hash(block) == block['hash']:
            print('invalid hash, got:' + block.hash)
            return False
        if not is_block_staking_valid(block['previous_hash'], block['staker_address'], block['staker_balance'], block['timestamp'], block['difficulty'], block['index']):
            print('staking hash not lower than balance over diffculty times 2^256')
            return False
        return True

    def add_block_to_chain(new_block):
        if is_valid_new_block(new_block, get_latest_block()):
            ret_val = process_transactions(new_block['transactions'], self.unspent_tx_outs(), new_block['index'])

        if (ret_val == null):
            return False
        else:
            self.chain.append(new_block)
            self.unspent_tx_outs = ret_val
            update_transaction_pool(unspent_tx_outs)
            return True

        return False

    def handle_received_transaction(self, transaction):
        add_to_transaction_pool(transaction, self.unspent_tx_outs())

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def consensus(self):
        replaced = self.resolve_conflicts()

        if replaced:
            self.save_db()
            response = {
                'message': 'Our chain was replaced',
                'new_chain': self.chain
            }
        else:
            response = {
                'message': 'Our chain is authoritative',
                'chain': self.chain
            }

        return jsonify(response), 200

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        genesis = chain[0]

        if genesis != genesis_block():
            return False

        for block_index in range(1, len(chain)):
            block = chain[block_index]
            last_block = chain[block_index - 1]
            if not self.valid_block(block, last_block):
                return False

        return True

    def valid_block(self, block, previous_block):

        """
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """
        if not is_valid_block_structure(block):
            print('invalid block structure: %s', json.dumps(block))
            return False

        if  previous_block['index'] + 1 != block['index']:
            return False
        elif previous_block != block['previous_hash']:
            return False
        elif not is_valid_timestamp(block, previous_block):
            return False
        elif self.hash(block) != block['hash']:
            return False
        return True

    def full_chain(self):
        response = {
            'chain': self.chain,
            'length': len(self.chain)

        }
        return response

    def replace_chain(self, chain):
        if self.valid_chain(chain) and get_accumulated_difficulty(chain) > get_accumulated_difficulty(self.chain):
            self.chain = chain
            a_unspent_tx_outs = []
            for block in chain:
                a_unspent_tx_outs = process_transactions(block['transactions'], a_unspent_tx_outs, block['index'])
                self.unspent_tx_outs = a_unspent_tx_outs
                update_transaction_pool(unspent_tx_outs)
            broadcast_latest()
        else:
            print('Received blockchain invalid')
            return False

    def get_accumulated_difficulty(a_blockchain):
        return seq(a_blockchain)\
                .map(lambda block : block['difficulty'])\
                .map(lambda difficulty : Math.pow(2, difficulty))\
                .reduce(lambda a, b : a + b)

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get('http://{}/chain'.format(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain["chain"]

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def save_db(self):
        if self.db is not None:
            db = shelve.open(self.db)
            db['chain'] = json.dumps(self.chain)
            db.close()

    def init_db(self, dbfile):
        self.db = dbfile
        db = shelve.open(self.db)
        try:
            if db['chain']:
                self.chain = json.loads(db['chain'])
                if len(self.chain) > 0:
                    self.block = self.chain[len(self.chain) - 1]
                    self.transactions = self.chain[len(self.chain) - 1]['transactions']
        except:
            db.close()
            self.save_db()

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def remove_nodes(self):
        """
        Clear nodes list.
        """
        self.nodes = set()

    def get_nodes(self):
        response = {
            'message': 'Nodes',
            'total_nodes': list(self.nodes),
        }
        return jsonify(response)

    def register_nodes(self, values):
        nodes = values.get('nodes')
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400

        for node in nodes:
            self.register_node(node)

        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(self.nodes),
        }
        return jsonify(response), 201
