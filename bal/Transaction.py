from functional import seq
from ecdsa import SigningKey, NIST192p
import numbers
import re
import json
import hashlib
from itertools import chain
from functools import reduce
COINBASE_AMOUNT = 50

class UnspentTxOut:
    def __init__(self, tx_out_id, tx_out_index, address, amount) :
        self.tx_out_id = tx_out_id
        self.tx_out_index = tx_out_index
        self.address = address
        self.amount = amount

    def to_json(self):
        return self.__dict__

class TxIn:
    def __init__(self, tx_out_id, tx_out_index, signature) :
        self.tx_out_id = tx_out_id
        self.tx_out_index = tx_out_index
        self.signature = signature

    def to_json(self):
        return self.__dict__

class TxOut:
    def __init__(self, address, amount):
        self.address = address
        self.amount = amount

    def to_json(self):
        return self.__dict__

class Transaction:
    def __init__(self, id, tx_ins, tx_outs):
        self.id = id
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs

    def to_json(self):
        return self.__dict__
        
def get_transaction_id(transaction):
    tx_in_content = ''.join(map(lambda tx_in : tx_in.tx_out_id + str(tx_in.tx_out_index), transaction.tx_ins))
    tx_out_content = ''.join(map(lambda tx_out : tx_out.address + str(tx_out.amount), transaction.tx_outs))
    encoded = '{}{}'.format(tx_in_content, tx_out_content).encode()
    return hashlib.sha256(encoded).hexdigest()

def validate_transaction(transaction, a_unspent_tx_outs):
    if not is_valid_transaction_structure(transaction):
        return False

    if get_transaction_id(transaction) != transaction.id:
        print('invalid tx id: ' + transaction.id)
        return False

    if not has_valid_tx_ins(transaction, a_unspent_tx_outs):
        print('some of the tx_ins are invalid in tx: ' + transaction.id)
        return False

    if total_tx_out_values(transaction) != total_tx_in_values(transaction, a_unspent_tx_outs):
        print('total_tx_out_values !== total_tx_in_values in tx: ' + transaction.id)
        return False

    return True

def validate_block_transactions(a_transactions, a_unspent_tx_outs, block_index):
    coinbase_tx = a_transactions[0]
    if not validate_coinbase_tx(coinbase_tx, block_index):
        print('invalid coinbase transaction: ' + json.dumps(coinbase_tx))
        return False

    tx_ins = seq(a_transactions)\
             .map(lambda tx : tx.tx_ins)\
             .flatten()

    if has_duplicates(tx_ins):
        return False

    normal_transactions = a_transactions[1:]
    return all(validate_transaction(tx, a_unspent_tx_outs) for tx in normal_transactions)

def validate_coinbase_tx(transaction, block_index):
    if not transaction:
        print('the first transaction in the block must be coinbase transaction')
        return False

    if get_transaction_id(transaction) != transaction.id:
        print('invalid coinbase tx id: ' + transaction.id)
        return False

    if len(transaction.tx_ins) != 1:
        print('one txIn must be specified in the coinbase transaction')
        return False

    if transaction.tx_ins[0].tx_out_index != block_index:
        print('the txIn signature in coinbase tx must be the block height')
        return False

    if len(transaction.tx_outs) != 1:
        print('invalid number of txOuts in coinbase transaction')
        return False

    if transaction.tx_outs[0].amount != COINBASE_AMOUNT:
        print('invalid coinbase amount in coinbase transaction')
        return False

    return True

def validate_tx_in(tx_in, transaction, a_unspent_tx_outs):
    referenced_u_tx_out = find_unspent_tx_out(tx_in.tx_out_id, tx_in.tx_out_index, a_unspent_tx_outs)

    if not referenced_u_tx_out == null:
        print('referenced txOut not found: ' + JSON.stringify(tx_in))
        return False

    address = referenced_u_tx_out.address

    key = VerifyingKey.from_der(bytes.from_hex(address))
    valid_signature = key.verify(tx_in.signature, transaction.id)
    if not valid_signature:
        print('invalid txIn signature: %s txId: %s address: %s', tx_in.signature, transaction.id, referenced_u_tx_out.address)
        return False

    return True

def new_coinbase_transaction(address, block_index):
    tx_in = TxIn('', block_index, '')

    t = Transaction(None, [tx_in], [TxOut(address, COINBASE_AMOUNT)])
    t.id = get_transaction_id(t)
    return t

def has_duplicates(tx_ins):
    tx_in_values = list(map(lambda tx_in : tx_in.tx_out_id + str(tx_in.tx_out_index), tx_ins))
    return len(set(tx_in_values)) != len(tx_in_values)

def sign_tx_in(transaction, tx_in_index, private_key, unspent_tx_outs):
    tx_in = transaction.tx_ins[tx_in_index]
    tx_to_sign = transaction.tx_id
    referenced_unspent_tx_out = find_unspent_tx_out(tx_in.tx_out_id, tx_in.tx_out_index, unspent_tx_outs)
    if not referenced_unspent_tx_out:
        print('could not find referenced txOut')
        raise

    signing_key = SigningKey.from_der(bytes.from_hex(private_key))
    if signing_key.get_verifying_key().to_der().hex() != referencedAddress:
        print('trying to sign an input with private' +
            ' key that does not match the address that is referenced in txIn')
        raise

    referenced_address = referenced_unspent_tx_out.address
    signature = signing_key.sign(tx_to_sign)
    return signature

def update_unspent_tx_outs(a_transactions, a_unspent_tx_outs):
    new_unspent_tx_outs = get_new_unspent_tx_outs(a_transactions)
    consumed_tx_outs = get_consumed_tx_outs(a_transactions)

    resulting_unspent_tx_outs = get_resulting_unspent_tx_outs(a_unspent_tx_outs, consumed_tx_outs)
    return resulting_unspent_tx_outs + new_unspent_tx_outs

def process_transactions(a_transactions, a_unspent_tx_outs, block_index):
    if not validate_block_transactions(a_transactions, a_unspent_tx_outs, block_index):
        print('invalid block transactions')
        return None

    return update_unspent_tx_outs(a_transactions, a_unspent_tx_outs)

def is_valid_tx_in_structure(tx_in):
    if not tx_in:
        print('txIn is null')
        return False
    elif type(tx_in.signature) != str:
        print('invalid signature type in txIn')
        return False
    elif type(tx_in.tx_out_id) != str:
        print('invalid txOutId type in txIn')
        return False
    elif not isinstance(tx_out.tx_out_index, numbers.Number):
        print('invalid txOutIndex type in txIn')
        return False
    else:
        return True

def is_valid_tx_out_structure(tx_out):
    if not tx_out:
        print('txOut is null')
        return False

    if type(tx_out.address) != str:
        print('invalid address type in txOut')
        return False

    if not is_valid_address(tx_out.address):
        print('invalid TxOut address')
        return False

    if not isinstance(tx_out.number, numbers.Number):
        print('invalid amount type in txOut')
        return False

    return True

def is_valid_transaction_structure(transaction):
    if type(transaction.id) != str:
        print('transactionId missing')
        return False

    if not isinstance(transaction.tx_ins, list):
        print('invalid txIns type in transaction')
        return False

    if not all(is_valid_tx_in_structure(tx_in) for tx_in in transaction.tx_ins):
        return False

    if not isinstance(transaction.tx_outs, list):
        print('invalid txIns type in transaction')
        return False

    if not all(is_valid_tx_out_structure(tx_out) for tx_out in transaction.tx_outs):
        return False

    return True

def is_valid_address(address):
    if address.length != 130:
        print(address)
        print('invalid public key length')
        return False
    elif not re.compile('^[a-fA-F0-9]+$').match(address):
        print('public key must contain only hex characters')
        return False
    return True

def get_new_unspent_tx_outs(new_transactions):
    result = []
    for transaction in new_transactions:
        tx_outs = transaction.tx_outs
        tx_objs = [UnspentTxOut(transaction.id, index, tx_out.address, tx_out.amount) for index, tx_out in enumerate(tx_outs)]
        result.extend(tx_objs)

    return result

def get_consumed_tx_outs(new_transactions):
    return seq(new_transactions)\
            .map(lambda t : t.tx_ins)\
            .reduce(lambda a, b : a.concat(b))\
            .map(lambda tx_in : UnspentTxOut(tx_in.tx_out_id, tx_in.tx_out_index, '',0))

def get_resulting_unspent_tx_outs(unspent_tx_outs, consumed_tx_outs):
    return [tx for tx in unspent_tx_outs if not find_unspent_tx_out(tx.tx_out_id, tx.tx_out_index, consumed_tx_outs)]

def has_valid_tx_ins(transaction):
    return seq(transaction.tx_ins)\
            .map(lambda tx_in : validate_tx_in(tx_in, transaction, a_unspent_tx_outs))\
            .reduce(lambda a, b : a and b, True)

def total_tx_in_values(transaction, a_unspent_tx_outs):
    return seq(transaction.tx_ins)\
            .map(lambda tx_in : get_tx_in_amount(tx_in, a_unspent_tx_outs))\
            .reduce(lambda a, b : (a + b), 0)

def total_tx_out_values(transaction):
    return seq(transaction.tx_outs)\
            .map(lambda tx_out : tx_out.amount)\
            .reduce(lambda a, b : (a + b), 0)

def find_unspent_tx_out(transaction_id, index, a_unspent_tx_outs):
    return next((x for u_tx_o in a_unspent_tx_outs if u_tx_o.tx_out_id == transaction_id and u_tx_o.tx_out_index == index), None)

def get_tx_in_amount(tx_in, a_unspent_tx_outs):
    return find_unspent_tx_out(tx_in.tx_out_id, tx_in.tx_out_index, a_unspent_tx_outs).amount
