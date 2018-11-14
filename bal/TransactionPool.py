from Transaction import Transaction, TxIn, UnspentTxOut, validate_transaction, find_unspent_tx_out
import copy

transaction_pool = []

def get_transaction_pool():
    return copy.deepcopy(transaction_pool)

def add_to_transaction_pool(tx, unspent_tx_outs):
    if not validate_transaction(tx, unspent_tx_outs):
        raise('Trying to add invalid tx to pool')

    if not is_valid_tx_for_pool(tx, transaction_pool):
        raise('Trying to add invalid tx to pool')

    print('adding to txPool: %s', json.dumps(tx))
    transaction_pool.append(tx)

def has_tx_in(tx_in, unspent_tx_outs):
    found_tx_in = find_unspent_tx_out(tx_in.tx_out_id, tx_in.tx_out_index, unspent_tx_outs)
    return bool(found_tx_in)

def update_transaction_pool(unspent_tx_outs):
    invalid_txs = []
    for tx in transaction_pool:
        for tx_in in tx.tx_ins:
            if not has_tx_in(tx_in, unspent_tx_outs):
                invalid_txs.append(tx)
                break
    if invalid_txs.length > 0:
        print('removing the following transactions from txPool: %s', json.dump(invalid_txs))
        transaction_pool = list(set(transaction_pool)-set(invalid_txs))

def get_tx_pool_ins(a_transaction_pool):
    return seq(a_transaction_pool)\
            .map(lambda tx : tx.tx_ins)\
            .flatten()

def is_valid_tx_for_pool(tx, a_transaction_pool):
    tx_pool_ins = get_tx_pool_ins(a_ttransaction_pool)

    for tx_in in tx.tx_ins:
        if has_tx_in(tx_in, tx_pool_ins):
            print('txIn already found in the txPool')
            return False

    return True
