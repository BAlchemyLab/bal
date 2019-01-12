from BaseBlockchain import BaseBlockchain
import numbers
from time import time
import hashlib

class POWBlockchain(BaseBlockchain):
    def genesis_block(self):
        return self.raw_block(0, 1465154705, '', [self.genesis_transaction()], self.get_initial_difficulty(), 0)


    def raw_block(self, index, timestamp, previous_hash, transactions, difficulty, proof):
        """
        Create a new Block in the Blockchain
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': index,
            'timestamp': timestamp,
            'previous_hash': previous_hash,
            'transactions': transactions,
            'difficulty': difficulty,
            'proof': proof
        }
        block['hash'] = self.hash(block)
        return block

    def is_block_proof_valid(self, block):
        guess_hash = block['hash']
        difficulty = block['difficulty']
        return guess_hash[:difficulty] == "0" * difficulty

    def find_block(self, index, previous_hash, transactions, difficulty):
        nonce = 0
        timestamp = time()
        while (True):
            temp_block = self.raw_block(index, timestamp, previous_hash, transactions, difficulty, nonce)
            if self.is_block_proof_valid(temp_block):
                return temp_block
            nonce += 1

    def is_valid_block_structure(self, block):
        return isinstance(block['index'], numbers.Number) and \
                 type(block['hash']) == str and \
                 type(block['previous_hash']) == str and \
                 isinstance(block['timestamp'], numbers.Number) and \
                 type(block['transactions']) == list and \
                 isinstance(block['difficulty'], numbers.Number) and \
                 isinstance(block['proof'], numbers.Number)

    def has_valid_hash(self, block):
        block_content = {x: block[x] for x in block if x != 'hash'}
        if not self.hash(block_content) == block['hash']:
            print('invalid hash, got:' + block['hash'])
            return False
        if not self.is_block_proof_valid(block):
            print('proof is not valid')
            return False
        return True
