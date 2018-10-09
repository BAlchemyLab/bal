# Python 3 -> 2 compatibility
from builtins import super
import requests

from BaseBlockChain import BaseBlockChain
import hashlib

DIFFICULTY_ADJUSTMENT_INTERVAL = 16
BLOCK_GENERATION_INTERVAL = 5

class POWBlockChain(BaseBlockChain):
    def __init__(self, initial_difficulty=4):
        super().__init__(initial_difficulty)
        print('POWBlockChain with initial difficulty=%d' % self.difficulty)
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
        self.difficulty = self.get_difficulty(self.chain)
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def full_chain(self):
        response = {
            'chain': self.chain,
            'length': len(self.chain)

        }
        return response

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

    def get_difficulty(self, a_block_chain):
        latest_block = a_block_chain[-1]
        if latest_block['index'] % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and latest_block['index'] != 0:
            return self.get_adjusted_difficulty(latest_block, a_block_chain)
        else:
            return latest_block['difficulty'];

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
