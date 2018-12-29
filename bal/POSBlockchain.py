from BaseBlockchain import BaseBlockchain
import numbers
from time import time
import hashlib
from Wallet import get_public_from_wallet

VALIDATING_WITHOUT_COIN = 10
DIFFICULTY_ADJUSTMENT_INTERVAL = 16 # block number
BLOCK_GENERATION_INTERVAL = 5 # in seconds
VALID_TIMESTAMP_INTERVAL = 60 # in seconds

class POSBlockchain(BaseBlockchain):
    def genesis_block(self):
        return self.raw_block(0, 1465154705, '', [self.genesis_transaction()], self.get_initial_difficulty(), 0, '0001')

    def raw_block(self, index, timestamp, previous_hash, transactions, difficulty, staker_balance, staker_address):
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
            'staker_balance': staker_balance,
            'staker_address': staker_address
        }
        block['hash'] = self.hash(block)
        return block

    def is_block_staking_valid(self, block):
        difficulty = block['difficulty'] + 1

        if block['index'] <= VALIDATING_WITHOUT_COIN:
            balance = block['staker_balance'] + 1
        else:
            balance = block['staker_balance']

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
                temp_block = self.raw_block(index, timestamp, previous_hash, transactions, difficulty, self.get_my_account_balance(), get_public_from_wallet())
                if self.is_block_staking_valid(temp_block):
                    return temp_block
                previous_time_stamp = timestamp

    def is_valid_block_structure(self, block):
        return isinstance(block['index'], numbers.Number) and \
                 type(block['hash']) == str and \
                 type(block['previous_hash']) == str and \
                 isinstance(block['timestamp'], numbers.Number) and \
                 type(block['transactions']) == list and \
                 isinstance(block['difficulty'], numbers.Number) and \
                 isinstance(block['staker_balance'], numbers.Number) and \
                 type(block['staker_address']) == str
