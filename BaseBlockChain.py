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


class BaseBlockChain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.db = None
        # Generate a globally unique address for this node
        self.node_identifier = str(uuid4()).replace('-', '')

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)
        pass

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

    @abc.abstractmethod
    def resolve_conflicts(self):
        return

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @abc.abstractmethod
    def proof_of(self, last_block):
        return

    @abc.abstractmethod
    def valid_block(self, last_proof, proof, last_hash):
        return

    @abc.abstractmethod
    def full_chain(self):
        return
