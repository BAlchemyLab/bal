# Python 3 -> 2 compatibility
try:  # Python 3
    from urllib.parse import urlparse
except:
    from urlparse import urlparse
from builtins import super

from BaseBlockChain import BaseBlockChain
import requests
import hashlib
from flask import jsonify, request


class QuantumBlockChain(BaseBlockChain):
    """
    BlockChain with proof based on QKD (Quantum Key Distribution) machinery.
    """

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.nodes = []
        self.keyworkers = []
        print("QuantumBlockChain")

        @app.route('/keyworker/register', methods=['POST'])
        def register_keyworkers():
            values = request.get_json()
            if values is None:
                return "Error: Please supply a valid list of keyworkers", 400
            keyworkers = values.get('keyworkers')
            if keyworkers is None:
                return "Error: Please supply a valid list of keyworkers", 400
            for keyworker in keyworkers:
                if self.register_keyworker(keyworker.get("address"), keyworker.get("device_num"), keyworker.get("id")):
                    return "Error: Failed to add", 400

            response = {
                'message': 'New keyworkers have been added',
                'total_nodes': list(self.keyworkers),
            }
            return jsonify(response), 200

        @app.route('/keyworker', methods=['DELETE'])
        def clear_keyworkers():
            keyworkers = []
            response = {
                'message': 'Keyworkers removed',
            }
            return jsonify(response)
 
        @app.route('/chain', methods=['POST'])
        def full_chain_post():
            values = request.get_json()
            if values is None:
                return "Wrong params", 400
            _keyworker_id = values.get("keyworker_id")
            if _keyworker_id is None:
                return "keyworker_id is empty", 400
            _keyworker = self.find_keyworker(_keyworker_id)
            if _keyworker is None:
                return "Failed to find keyworker by id", 400
            _do_resolve = True
            for _node in values.get("path"):
                if _node == self.node_identifier:
                    _do_resolve = False
                    break
            if _do_resolve:
                self.resolve_conflicts(path=values.get("path"))
            return jsonify(self.full_chain_quantum(_keyworker)), 201

    def register_keyworker(self, address, device_num, id):
        """
        Add a new keyworker to the list of keyworkers
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        :param device_num: Number of device Eg. 0
        :param id: Id of keyworker Eg. 0
        """
        if device_num is None:
            _device_num = -1
        else:
            _device_num = device_num
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            _address = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            _address = parsed_url.path
        else:
            return 1
        if not self.find_keyworker(id) is None:
            return 2
        kw = {
            'device_num': _device_num,
            'address': _address,
            'id': id
        }
        self.keyworkers.append(kw)
        return 0

    def find_keyworker(self, keyworker_id):
        for val in self.keyworkers:
            if val['id'] == keyworker_id:
                return val
        return None

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address and keyworker of node. Eg. '{"address":"http://127.0.0.1:5001","keyworker_id":0}'
        """
        _address = address.get("address")
        _keyworker_id = address.get("keyworker_id")
        parsed_url = urlparse(_address)
        if parsed_url.netloc:
            self.nodes.append({"address": parsed_url.netloc, "keyworker_id": _keyworker_id})
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.append({"address": parsed_url.path, "keyworker_id": _keyworker_id})
        else:
            raise ValueError('Invalid URL')

    def remove_nodes(self):
        """
        Clear nodes list.
        """
        self.nodes = []

    def getlastkey(self, keyworker):
        """
        :param keyworker: keyworker for work with
        """
        if keyworker["device_num"]>=0:
            data = "last"+str(keyworker["id"])
        else:
            data = "last"
        try:
            response = requests.post('http://{}'.format(keyworker["address"]), data=data)
            response.raise_for_status()
        except:
            print("ERROR IN POST getlastkey")
            return 0
        block_string = bytearray.fromhex(response.text)
        hash256 = hashlib.sha256(block_string).hexdigest().upper()
        key = {
            'key': response.text,
            'sha': hash256
        }
        return key

    def getkeybysha(self, sha, keyworker):
        try:
            response = requests.post('http://{}'.format(keyworker["address"]), data="key{}".format(sha))
            response.raise_for_status()
        except:
            print("ERROR IN POST getkeybysha")
            return 0
        key = {
            'key': response.text,
            'sha': sha
        }
        return key

    def valid_chain(self, chain, keyworker):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :param keyworker: keyworker for work with
        :return: True if valid, False if not
        """
        quantum_proof = chain["quantum_proof"]
        quantum_hash = chain["quantum_hash"]
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
                print("error in consistency")
                return False

            last_block = block
            current_index += 1

        quantum_key = self.getkeybysha(quantum_hash, keyworker)
        if quantum_key == 0:
            print("NO SUCH KEY")
            return False
        guess = '{}{}'.format(chain[-1]["proof"], quantum_key["key"]).encode()
        guess_proof = hashlib.sha256(guess).hexdigest()
        return guess_proof == quantum_proof

    def proof_of(self, last_block):
        """
        Simple Proof of QKD Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        raw_proof = '{}{}'.format(last_proof, last_hash).encode()
        proof = hashlib.sha256(raw_proof).hexdigest()
        return proof

    def valid_block(self, last_proof, proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.

        """

        guess = '{last_proof}{last_hash}'.format(last_proof=last_proof, last_hash=last_hash).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash == proof

    def full_chain_quantum(self, keyworker):
        quantum_key = self.getlastkey(keyworker)
        guess = '{}{}'.format(self.chain[-1]["proof"], quantum_key["key"]).encode()
        guess_proof = hashlib.sha256(guess).hexdigest()
        response = {
            'chain': self.chain,
            'length': len(self.chain),
            'quantum_hash': quantum_key['sha'],
            'quantum_proof': guess_proof
        }
        return response

    def full_chain(self):
        response = {
            'chain': self.chain,
            'length': len(self.chain)
        }
        return response

    def resolve_conflicts(self, *args, **kwargs):
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
            _address = node["address"]
            _keyworker_id = node["keyworker_id"]
            keyworker = self.find_keyworker(_keyworker_id)
            if keyworker is None:
                print("Cannot find keyworker by id")
                continue
            path = kwargs.get('path', None)
            if path is None:
                json = {"path": [self.node_identifier], "keyworker_id": _keyworker_id}
            else:
                #Verify loops
                for _node in path:
                    if _node == self.node_identifier:
                        return False
                path.append(self.node_identifier)
                json = {"path": path, "keyworker_id": _keyworker_id}
            response = requests.post('http://{}/chain'.format(_address), json=json)
            if response.status_code == 201:
                length = response.json()['length']
                chain = response.json()
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain, keyworker):
                    max_length = length
                    new_chain = chain["chain"]

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False
