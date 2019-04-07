from POSBlockchain import POSBlockchain
import numbers
from time import time
import hashlib

class POSBlockchainSimulation(POSBlockchain):
    def __init__(self, p2p_port, initial_difficulty, simulation_path, name):
        super(POWBlockchainSimulation, self).__init__(p2p_port, initial_difficulty)
        self.path = simulation_path
        self.name = name

    def before_send_transaction(self, tx):
        ts = time()
        tx_id = tx['id']
        with open(self.path + 'transaction-'+tx_id+'.txt', 'w') as file:
            file.write(self.name + '---'+ 'Sending transaction id:' + tx_id + '---' + str(int(ts)))
            file.write('\n')

    def before_handle_received_transaction(self, tx):
        ts = time()
        tx_id = tx['id']
        with open(self.path + 'transaction-'+tx_id+'.txt', 'a+') as file:
            file.write(self.name + '---'+ 'received transaction id:' + tx_id + '---' + str(int(ts)))
            file.write('\n')
