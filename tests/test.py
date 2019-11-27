import unittest
from bal.transaction import *

class TestTransactionMethods(unittest.TestCase):


    def test_new_unspent_tx_out(self):

        example_new_unspent_tx_out = new_unspent_tx_out("testId27", 0, "testAddress66", 500)

        intended_result = {'tx_out_id': 'testId27', 'tx_out_index': 0, 'address': 'testAddress66', 'amount': 500}

        self.assertEqual(intended_result, example_new_unspent_tx_out)


    def test_new_tx_in(self):

        example_new_tx_in = new_tx_in("testId27", 0, "testSignature76")

        intended_result = {'tx_out_id': 'testId27', 'tx_out_index': 0, 'signature': 'testSignature76'}

        self.assertEqual(intended_result, example_new_tx_in)


    def test_new_tx_out(self):

        example_new_tx_out = new_tx_out("testAddress66", 500)

        intended_result = {'address': 'testAddress66', 'amount': 500}

        self.assertEqual(intended_result, example_new_tx_out)


    def test_new_transaction(self):
        example_new_tx_in_1 = new_tx_in("testId270", 0, "testSignature760")
        example_new_tx_in_2 = new_tx_in("testId271", 1, "testSignature761")
        example_new_tx_ins = [example_new_tx_in_1, example_new_tx_in_2]
        example_new_tx_out_1 = new_tx_out("testAddress660", 500)
        example_new_tx_out_2 = new_tx_out("testAddress661", 501)
        example_new_tx_outs = [example_new_tx_out_1, example_new_tx_out_2]
        example_new_transaction = new_transaction("testId28", example_new_tx_ins, example_new_tx_outs)

        intended_result = {'id': 'testId28',
        'tx_ins': [{'tx_out_id': 'testId270', 'tx_out_index': 0, 'signature': 'testSignature760'},
        {'tx_out_id': 'testId271', 'tx_out_index': 1, 'signature': 'testSignature761'}],
        'tx_outs': [{'address': 'testAddress660', 'amount': 500}, {'address': 'testAddress661', 'amount': 501}]}

        self.assertEqual(intended_result,
        example_new_transaction)

    def test_get_transaction_id(self):
        example_new_tx_in_1 = new_tx_in("testId270", 0, "testSignature760")
        example_new_tx_in_2 = new_tx_in("testId271", 1, "testSignature761")
        example_new_tx_ins = [example_new_tx_in_1, example_new_tx_in_2]
        example_new_tx_out_1 = new_tx_out("testAddress660", 500)
        example_new_tx_out_2 = new_tx_out("testAddress661", 501)
        example_new_tx_outs = [example_new_tx_out_1, example_new_tx_out_2]
        example_new_transaction = new_transaction("testId28", example_new_tx_ins, example_new_tx_outs)
        example_get_transaction_id = get_transaction_id(example_new_transaction)

        intended_result = "498d1fd4386ac8f5c0dcf6cda9154f901df632021b7fc11c9ab4398535fc9dd2"

        self.assertEqual(intended_result,
        example_get_transaction_id)

    # def test_validate_transaction(self):
    #
    #     example_new_tx_in_1 = new_tx_in("testId270", 0, "testSignature760")
    #     example_new_tx_in_2 = new_tx_in("testId271", 1, "testSignature761")
    #     example_new_tx_ins = [example_new_tx_in_1, example_new_tx_in_2]
    #     example_new_tx_out_1 = new_tx_out("testAddress660", 500)
    #     example_new_tx_out_2 = new_tx_out("testAddress661", 501)
    #     example_new_tx_outs = [example_new_tx_out_1, example_new_tx_out_2]
    #     example_new_transaction = new_transaction("testId28", example_new_tx_ins, example_new_tx_outs)
    #     ### work in progress






if __name__ == '__main__':
    unittest.main()
