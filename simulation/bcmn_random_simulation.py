#!/usr/bin/env python

import sys
import yaml
import json

from time import sleep, time
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host, CPULimitedHost, OVSBridge, Switch
from mininet.util import specialClass
from mininet.link import TCLink
from mininet.term import makeTerms
from bal.bcnode import POWNode, POSNode
from bal.BaseBlockchain import BLOCK_GENERATION_INTERVAL
from bal.transaction import COINBASE_AMOUNT
import random_topology_generator as rtg
import random
import os
from mininet.log import setLogLevel
import shutil
import getopt
import traceback
from argparse import ArgumentParser
from bcmn_simulation import *
from simulation_tools import *

def simulate(host_type, host_number, miner_percentages, transaction_counts, simulation_count, root_path, debug_mode):
    adj_matrix = rtg.random_connected_graph(host_number, edge_number, 100)
    G = nx.parse_edgelist(edge_list, nodetype = int)
    net_params = {'topo': None, 'build': False, 'host': host_type, 'switch': OVSBridge,
                    'link': TCLink, 'ipBase': '10.0.0.0/8', 'waitConnected' : True,
                    'xterms': debug_mode}

    for miner_percentage, transaction_count in itertools.product(miner_percentages, transaction_counts):
        for i in range(0, simulation_count):
            print("Simulating with miner %: + " miner_percentage + "transaction #:" + transaction_count)
            parametered_path = 'h' + str(host_number) + 'm' + str(miner_percentage) + 't' + str(transaction_count)
            path = root_path + parametered_path

            switch_number = host_number / 4
            max_bw = 100

            net = rtg.random_topology(switch_number, host_number, max_bw, net_params)

            miner_number = (len(net.hosts)*miner_percentage / 100) || 1
            miners = random.sample(net.hosts, miner_number)
            transactors = [random.choice(net.hosts) for x in range(transaction_count)]
            subsimulation(adj_matrix, net, host_number, miners, transactors, path, debug_mode)

def subsimulation(adj_matrix, net, host_number, miners, transactors, sim_path, debug_mode):
    try:
        start_time = time()
        timestamp_str = str(int(start_time))

        verifier = random.choice(net.hosts)
        ts_dir_path = init_simulation_path(sim_path + '/' + timestamp_str + '/')

        net.build()
        net.start()

        for node in net.hosts:
            node.start(ts_dir_path)

        sleep(2) # Wait for nodes to be started completely.

        peer_topology = register_peer_topology(net)

        edge_list = rtg.graph_to_str(adj_matrix)
        dump_graph(edge_list, ts_dir_path)
        dump_net(net, peer_topology, miners, ts_dir_path)

        transaction_count = len(transactors)
        target_amount = transaction_count * COINBASE_AMOUNT
        for node in net.hosts:
            node.call('block/generate/loop/start', True)

        print("Waiting for block generations for initial target amounts.")
        generated = []

        while len(generated) != len(net.hosts):
            sleep(BLOCK_GENERATION_INTERVAL)
            print('***** AMOUNT CONTROL *****')
            for h in net.hosts:
                if h.name in generated:
                    continue
                host_amount = verifier_check_amount(h, verifier)
                print(h.name + ' has ' + str(host_amount) + ' coins currently, target is: ' + str(target_amount))
                if (host_amount >= target_amount):
                    print(h.name + ' has enough coins, stopping generation for it')
                    h.call('block/generate/loop/stop', True)
                    generated.append(h.name)

        for miner in miners:
            miner.call('block/generate/loop/start', True)

        i = 0
        temp_block_number = 0
        while i < transaction_count:
            sender = random.choice(transactors)
            receiver = random.choice(net.hosts)
            current_block_number = yaml.safe_load(sender.call('chain/length', True))
            while current_block_number <= temp_block_number:
                sleep(BLOCK_GENERATION_INTERVAL)
                current_block_number = yaml.safe_load(sender.call('chain/length', True))

            if send_and_log_transaction(sender, receiver, 1, ts_dir_path):
                i = i + 1
                sleep(1)
                temp_block_number = yaml.safe_load(sender.call('chain/length', True))

        print('Waiting for nodes to receive transactions')
        while not check_block_txts(ts_dir_path, host_number, transaction_count):
            sleep(0.5)

        elapsed_time = time() - start_time
        dump_elapsed_time(elapsed_time, ts_dir_path)
        dump_chain(verifier, ts_dir_path)
        net.stop()
        move_txs_to_directories(ts_dir_path)
    except:
        if net:
            open_mininet_cli(net)
            net.stop()
        traceback.print_exc()


def main():
    host_type = None
    parser = ArgumentParser()
    parser.add_argument('-ht', '--host_type', default='pow', type=str, help='blockchain consensus class to be used')
    parser.add_argument('-p', '--path', default='/tmp/', type=str, help='where the logs will be located. default: /tmp/')
    parser.add_argument('-d', '--debug', default=False, help='debug mode for xterms.', action='store_true')
    parser.add_argument('-s', '--setup', default=False, help='go with setup mode for h=10,20,50,100 m=10,20,50,80 tx=10, sim=10', action='store_true')
    args = parser.parse_args()
    tmp_location = '/tmp/bcn'
    if os.path.exists(tmp_location):
        shutil.rmtree('/tmp/bcn')
    setLogLevel( 'info' )

    if args.host_type.find('pos') == 0:
        host_type = POSNode
    else:
        host_type = POWNode

    #make this separate arguments
    if args.setup:
        host_numbers = [10, 20, 50, 100]
        miner_percentages = [0, 10, 25, 50, 100]
        transaction_counts = [1, 5, 10]
        simulation_count = 5
        for host_number in host_numbers:
            simulate(host_type, host_number, miner_percentages, transaction_counts, simulation_count, args.path, args.debug)

    else:
        host_number = int(input("Number of hosts(>10):"))
        miner_percentage = int(input("Miner percentage (0-100):"))
        transaction_count = int(input("Number of repeated random transactions:"))
        simulation_count = int(input("Number of repeated simulations:"))
        simulate(host_type, host_number, [miner_percentage], [transaction_count], simulation_count, args.path, args.debug)
if __name__ == '__main__':
    main()
