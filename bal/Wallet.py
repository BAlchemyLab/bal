from ecdsa import SigningKey, NIST192p
from Transaction import get_transaction_id, sign_tx_in, Transaction, TxIn, TxOut, UnspentTxOut
import numbers
import os

PRIVATE_KEY_LOCATION = 'private_key.pem'

def get_private_from_wallet():
    sk = SigningKey.from_pem(open(PRIVATE_KEY_LOCATION).read())
    return sk

def get_public_from_wallet():
    private_key = get_private_from_wallet()
    key = SigningKey.from_string(private_key, curve=NIST192p)
    return key.get_verifying_key().to_pem()

def generate_private_key():
    private_key = SigningKey.generate(curve=NIST192p)
    return private_key.to_pem()

def init_wallet():
    if os.path.exists(PRIVATE_KEY_LOCATION):
        return

    new_private_key = generate_private_key()
    f = open(PRIVATE_KEY_LOCATION, "x")
    f.write(new_private_key)
    f.close()
    print('new wallet with private key created to : %s', PRIVATE_KEY_LOCATION)

def delete_wallet():
    if os.path.exists(PRIVATE_KEY_LOCATION):
      os.remove(PRIVATE_KEY_LOCATION)
    else:
      print("The file does not exist")


def get_balance(address, unspent_tx_outs):
    return seq(find_unspent_tx_outs(address, unspent_tx_outs))\
            .map(lambda u_tx_o: u_tx_o.amount)\
            .sum()

def find_unspent_tx_outs(owner_address, unspent_tx_outs):
    return filter(lambda u_tx_o : u_tx_o.address == owner_address, unspent_tx_outs)

def find_tx_outs_for_amount(amount, my_unspent_tx_outs):
    current_amount = 0
    included_unspent_tx_outs = []
    for my_unspent_tx_out in my_unspent_tx_outs:
        included_unspent_tx_outs.append(my_unspent_tx_out)
        current_amount = current_amount + my_unspent_tx_out.amount
        if current_amount >= amount:
            left_over_amount = current_amount - amount
            return [included_unspent_tx_outs, left_over_amount]

    eMsg = 'Cannot create transaction from the available unspent transaction outputs.' + \
        ' Required amount:' + amount + '. Available unspentTxOuts:' + json.dump(myUnspentTxOuts)
    raise(eMsg)

def create_tx_outs(receiver_address, my_address, amount, left_over_amount):
    tx_out1 = TxOut(receiver_address, amount)
    if left_over_amount == 0:
        return [tx_out1]
    else:
        left_over_tx = TxOut(my_address, left_over_amount)
        return [tx_out1, left_over_tx]

def filter_tx_pool_txs(unspent_tx_outs, transaction_pool):
    tx_ins = seq(transaction_pool)\
                .map(lambda tx : tx.tx_ins)\
                .flatten()
    removable = []
    for unspent_tx_out in unspent_tx_outs:
        tx_in = find_unspent_tx_out(unspent_tx_out.tx_out_id, unspent_tx_out.tx_out_index, tx_ins)
        if tx_in:
            removable.append(unspent_tx_out)

    return list(set(unspent_tx_outs)-set(removable))

def create_transaction(receiver_address, amount, private_key, unspent_tx_outs, tx_pool):
    print('txPool: %s', json.dump(txPool))
    key = SigningKey.from_string(private_key, curve=NIST192p)
    myAddress = key.get_verifying_key().to_string()
    my_unspent_tx_outs_a = find_unspent_tx_outs(my_address, unspent_tx_outs)

    my_unspent_tx_outs = filter_tx_pool_txs(my_unspent_tx_outs_a, tx_pool)

    included_unspent_tx_outs, left_over_amount = find_tx_outs_for_amount(amount, my_unspent_tx_outs)


    unsigned_tx_ins = map(lambda utx_o : TxIn(utx_o.tx_out_id, utx_o.tx_out_index, None), included_unspent_tx_outs)

    tx_ins = unsigned_tx_ins
    tx_outs = create_tx_outs(receiver_address, my_address, amount, left_over_amount)

    tx = Transaction(None, tx_ins, tx_outs)
    tx_id = get_transaction_id(tx)
    tx.id = tx_id

    for index, tx_in in enumarate(tx.tx_ins):
        tx_in.signature = sign_tx_in(tx, index, private_key, unspent_tx_outs)

    return tx
