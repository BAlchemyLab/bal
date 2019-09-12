from bal.variant.base_blockchain import BaseBlockchain
import numbers
from time import time
import hashlib
from bal.wallet import get_public_from_wallet
from bal.transaction import COINBASE_AMOUNT

VALIDATING_WITHOUT_COIN = 10
NO_STAKE_HELP_RATE = 10.0

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
            if balance == 0:
                stake_helper = COINBASE_AMOUNT / NO_STAKE_HELP_RATE
                balance = stake_helper


        balance_over_difficulty = (2**256) * balance/(difficulty * 1.0)
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

    def has_valid_hash(self, block):
        block_content = {x: block[x] for x in block if x != 'hash'}
        if not self.hash(block_content) == block['hash']:
            print('invalid hash, got:' + block['hash'])
            return False
        if not self.is_block_staking_valid(block):
            print('staking hash not lower than balance over diffculty times 2^256')
            print('invalid hash, got:' + block['hash'])
            return False
        return True
