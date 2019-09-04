from bal.variant.pos_blockchain import POSBlockchain
import numbers
from time import time
import hashlib

class POSBlockchainSimulation(POSBlockchain):
    def __init__(self, p2p_port, initial_difficulty, simulation_path, name):
        super(POSBlockchainSimulation, self).__init__(p2p_port, initial_difficulty)
        self.path = simulation_path
        self.name = name


    def before_send_transaction(self, tx):
        ts = time()
        tx_id = tx['id']
        with open(self.path + 'transaction_pool-'+tx_id+'.txt', 'w') as file:
            file.write(self.name + '---'+ 'sending tx' + '---' + str(ts))
            file.write('\n')

    def before_handle_received_transaction(self, tx):
        ts = time()
        tx_id = tx['id']
        with open(self.path + 'transaction_pool-'+tx_id+'.txt', 'a+') as file:
            file.write(self.name + '---'+ 'received tx' + '---' + str(ts))
            file.write('\n')

    def after_generate_raw_next_block(self, block):
        ts = time()
        transactions = block['transactions']
        if len(transactions) > 1:
            for tx in transactions[1:]:
                tx_id = tx['id']
                with open(self.path + 'transaction_block-'+tx_id+'.txt', 'w') as file:
                    file.write(self.name + '---'+ 'sending tx with block' + '---' + str(ts))
                    file.write('\n')

    def before_update_chain(self, block):
        ts = time()
        transactions = block['transactions']
        for tx in transactions[1:]: #ignore coinbase transaction
            tx_id = tx['id']
            with open(self.path + 'transaction_block-'+tx_id+'.txt', 'a+') as file:
                file.write(self.name + '---'+ 'received tx with block' + '---' + str(ts))
                file.write('\n')
