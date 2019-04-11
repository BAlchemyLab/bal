from Transaction import new_transaction, new_tx_in, new_unspent_tx_out, validate_transaction, find_unspent_tx_out
import copy
import json
from functional import seq

class TransactionPool:
    def __init__(self):
        self.transaction_pool = []

    def get_transaction_pool(self):
        return copy.deepcopy(self.transaction_pool)

    def add_to_transaction_pool(self, tx, unspent_tx_outs):
        if not validate_transaction(tx, unspent_tx_outs):
            raise Exception('Trying to add invalid tx to pool: ' + json.dumps(tx))

        if not self.is_valid_tx_for_pool(tx):
            raise Exception('Trying to add same tx to pool')

        print('adding to txPool: %s', json.dumps(tx))
        self.transaction_pool.append(tx.copy())

    def has_tx_in(self, tx_in, unspent_tx_outs):
        found_tx_in = find_unspent_tx_out(tx_in['tx_out_id'], tx_in['tx_out_index'], unspent_tx_outs)
        return bool(found_tx_in)

    def update_transaction_pool(self, unspent_tx_outs):
        invalid_txs = []
        for tx in self.transaction_pool:
            for tx_in in tx['tx_ins']:
                if not self.has_tx_in(tx_in, unspent_tx_outs):
                    invalid_txs.append(tx)
                    break
        if len(invalid_txs) > 0:
            print('removing the following transactions from txPool: %s', json.dumps(invalid_txs))
            self.transaction_pool = [tx for tx in self.transaction_pool if tx not in invalid_txs]

    def get_tx_pool_ins(self):
        return seq(self.transaction_pool)\
                .map(lambda tx : tx['tx_ins'])\
                .flatten()

    def is_valid_tx_for_pool(self, tx):
        tx_pool_ins = self.get_tx_pool_ins()

        for tx_in in tx['tx_ins']:
            if self.has_tx_in(tx_in, tx_pool_ins):
                print('txIn already found in the txPool')
                return False

        return True
