import socket, select, pickle, threading
from enum import Enum
from time import sleep
import json
import struct
import traceback

class MessageType(Enum):
    QUERY_LATEST_BLOCK = 0
    QUERY_ALL = 1
    RESPONSE_BLOCKCHAIN = 2
    QUERY_TRANSACTION_POOL = 3
    RESPONSE_TRANSACTION_POOL = 4

class Message:
    def __init__(self, message_type, message_data, reply_addr):
        self.type = message_type
        self.data = message_data
        self.reply_addr = reply_addr

class P2P:
    def __init__(self, node, socket):
        self.p2p_addr = ('', socket)
        self.node = node
        self.peer_sockets = {}
        self.p2p_socket = None

    def blockchain(self):
        return self.node

    def transaction_pool(self):
        return self.node.transaction_pool

    def query(self, peer_addr, message):
        threading.Thread(
                target = self.send_message,
                args = (peer_addr, message)
        ).start()

    def add_peer(self, peer_str):
        peer_addr = self.get_peer_tuple(peer_str)
        if peer_str in self.peer_sockets.values():
            return False
        else:
            self.query(peer_addr, Message(MessageType.QUERY_LATEST_BLOCK, '', self.p2p_addr))
            sleep(0.5)
            self.query(peer_addr, Message(MessageType.QUERY_TRANSACTION_POOL, '', self.p2p_addr))
            return True

    def get_peers(self):
        return list(self.peer_sockets.keys())

    def broadcast_latest(self):
        """Broadcasts the latest block in the chain to connected peers, which
        will request the entire chain if needed"""
        for peer_str in self.peer_sockets:
            peer_addr = self.get_peer_tuple(peer_str)
            self.query(peer_addr, Message(MessageType.RESPONSE_BLOCKCHAIN, [self.blockchain().get_latest_block()], self.p2p_addr))

    def broadcast_transaction_pool(self):
        """Broadcasts the latest block in the chain to connected peers, which
        will request the entire chain if needed"""
        for peer_str in self.peer_sockets:
            peer_addr = self.get_peer_tuple(peer_str)
            self.query(peer_addr, Message(MessageType.RESPONSE_TRANSACTION_POOL, self.transaction_pool().get_transaction_pool(), self.p2p_addr))

    def send_message(self, peer_addr, data):
        """Sends a message with provided data to a given address, opening a new
        p2p socket if neccesary"""
        try:
            peer_str = self.get_peer_str(peer_addr)
            if not peer_str in self.peer_sockets or True:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect(peer_addr)
                self.peer_sockets[peer_str] = peer_socket
            else:
                peer_socket = self.peer_sockets[peer_str]
                peer_socket.connect(peer_addr)
            dumped_data = pickle.dumps(data)
            msg = struct.pack('>I', len(dumped_data)) + dumped_data
            peer_socket.sendall(msg)
        except Exception:
            pass

    def process_response_chain(self, message):
        """Given a message with blockchain response, validates the result and
        either updates the local blockchain, requests more data, or rejects
        the response chain"""
        received_chain = message.data
        if len(received_chain) == 0:
            print('Received zero-length chain from {}'.format(message.reply_addr[1]))
            return

        latest_received_block = received_chain[len(received_chain) - 1]
        try:
            self.blockchain().is_valid_block_structure(latest_received_block)
        except ValueError:
            print('Received invalid chain from {}'.format(message.reply_addr[1]))
            return

        current_latest_block = self.blockchain().get_latest_block()
        if latest_received_block['index'] > current_latest_block['index']:
            if latest_received_block['previous_hash'] == current_latest_block['hash']:
                self.blockchain().add_block_to_chain(latest_received_block)
                print('Received one block from {}'.format(message.reply_addr[1]))
                self.broadcast_latest()
            elif len(received_chain) == 1:
                self.query(message.reply_addr, Message(MessageType.QUERY_ALL, '', self.p2p_addr))
                print('Chain far behind {}, requesting entire chain'.format(message.reply_addr[1]))
            elif self.blockchain().replace_chain(received_chain):
                print('Received updated chain from {}'.format(message.reply_addr[1]))
                self.broadcast_latest()
        else:
            print('Received chain from {} not longer than current chain'.format(message.reply_addr[1]))

    def get_peer_str(self, peer_tuple):
        return ':'.join(map(str,peer_tuple))

    def get_peer_tuple(self, peer_str):
        vals = peer_str.split(':')
        address = vals[0]
        port = int(vals[1])
        return (address, port)

    def recv_msg(self, sock):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(sock, msglen)

    def recvall(self, sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def start(self):
        self.p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.p2p_socket.bind(self.p2p_addr)
        self.p2p_socket.listen(5)
        while True:
            conn_socket, addr = self.p2p_socket.accept()

            message = self.recv_msg(conn_socket)
            try:
                message = pickle.loads(message)

                peer_addr = (addr[0], message.reply_addr[1])
                message.reply_addr = peer_addr
                peer_str = self.get_peer_str(peer_addr)
                if not peer_str in self.peer_sockets:
                    self.query(peer_addr, Message(MessageType.QUERY_LATEST_BLOCK, '', self.p2p_addr))
                    print('Added new peer {}'.format(peer_str))

                if message.type == MessageType.RESPONSE_BLOCKCHAIN:
                    self.process_response_chain(message)
                elif message.type == MessageType.QUERY_ALL:
                    print('Dispatching all blocks to {}'.format(message.reply_addr[1]))
                    self.query(peer_addr, Message(MessageType.RESPONSE_BLOCKCHAIN, self.blockchain().get_blockchain(), self.p2p_addr))
                elif message.type == MessageType.QUERY_LATEST_BLOCK:
                    print('Dispatching latest block to {}'.format(message.reply_addr[1]))
                    self.query(peer_addr, Message(MessageType.RESPONSE_BLOCKCHAIN, [self.blockchain().get_latest_block()], self.p2p_addr))
                elif message.type == MessageType.QUERY_TRANSACTION_POOL:
                    self.query(peer_addr, Message(MessageType.RESPONSE_TRANSACTION_POOL, self.transaction_pool().get_transaction_pool(), self.p2p_addr))
                elif message.type == MessageType.RESPONSE_TRANSACTION_POOL:
                    received_transactions = message.data
                    if not received_transactions:
                        print('invalid transaction received: %s', json.dumps(message.data))
                        pass

                    for transaction in received_transactions:
                        try:
                            self.blockchain().handle_received_transaction(transaction)
                            self.broadcast_transaction_pool()
                        except Exception as e:
                            print(str(e))
            except pickle.UnpicklingError as e:
                traceback.print_exc()
                pass

        self.p2p_socket.close()
