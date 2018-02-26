# Python 3 -> 2 compatibility
from builtins import super

from BaseBlockChain import BaseBlockChain
import hashlib


class POWBlockChain(BaseBlockChain):
    def __init__(self, difficulty=4):
        super().__init__()
        self.difficulty = difficulty
        print('POWBlockChain with difficulty=%d' % self.difficulty)
        return

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """
        chain = chain["chain"]
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('{}'.format(last_block))
            print('{}'.format(block))
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_block(last_block['proof'], block['proof'], block['previous_hash']):
                return False

            last_block = block
            current_index += 1

        return True

    def proof_of(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_block(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    def valid_block(self, last_proof, proof, last_hash):

        """
        Validates the Proof
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """

        guess = '{}{}{}'.format(last_proof, proof, last_hash).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def full_chain(self):
        response = {
            'chain': self.chain,
            'length': len(self.chain)

        }
        return response
