#!/usr/bin/env python

import sys
import yaml
import json

from time import sleep, time
from mininet.topo import SingleSwitchTopo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host, CPULimitedHost, OVSKernelSwitch, Switch
from mininet.util import specialClass
from mininet.link import TCLink
from mininet.term import makeTerms
from bal.bcnode import POWNode, POSNode
from bal.BaseBlockchain import BLOCK_GENERATION_INTERVAL
import random_topology_generator as rtg
import random
import os
from functools import partial
from mininet.log import setLogLevel
import shutil
import getopt
import traceback
from argparse import ArgumentParser
from bcmn_simulation import *
from simulation_tools import *

def simulate(host_type, host_number, miner_percentage, number_of_transactions, root_path, debug_mode):
    net = None
    try:
        start_time = time()
        timestamp_str = str(int(start_time))
        net_params = {'topo': None, 'build': False, 'host': host_type, 'switch': OVSKernelSwitch,
                        'link': TCLink, 'ipBase': '10.0.0.0/8', 'waitConnected' : True, 'xterms': debug_mode}

        switch_number = host_number / 4
        max_bw = 100

        net = rtg.random_topology(switch_number, host_number, max_bw, net_params)
        net.build()
        net.start()

        verifier = random.choice(net.hosts)
        parametered_path = 'h' + str(host_number) + 'm' + str(miner_percentage)
        ts_dir_path = init_simulation_path(root_path + parametered_path + '/' + timestamp_str + '/')

        for node in net.hosts:
            node.start(ts_dir_path)

        sleep(2) # Wait for nodes to be started completely.

        peer_topology = register_peer_topology(net)
        miner_number = (len(net.hosts)*miner_percentage / 100)

        miners = random.sample(net.hosts, miner_number)

        dump_net(net, peer_topology, miners, ts_dir_path)

        target_amount = 2
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
        while i < number_of_transactions:
            sender, receiver = random.sample(net.hosts, 2)
            if send_and_log_transaction(sender, receiver, 1, ts_dir_path):
                i = i + 1
                sleep(1)

        print('Waiting for nodes to receive transactions')
        while not check_block_txts(ts_dir_path, host_number, number_of_transactions):
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
        miner_percentages = [10,20,50,80]
        number_of_transactions = 10
        number_of_simulations = 10
        for pair in itertools.product(host_numbers, miner_percentages):
            for i in range(0, number_of_simulations):
                simulate(host_type, pair[0], pair[1], number_of_transactions, args.path, args.debug)

    else:
        host_number = int(input("Number of hosts(>10):"))
        miner_percentage = int(input("Miner percentage (0-100):"))
        number_of_transactions = int(input("Number of repeated random transactions:"))
        number_of_simulations = int(input("Number of repeated simulations:"))
        for i in range(0, number_of_simulations):
            simulate(host_type, host_number, miner_percentage, number_of_transactions, args.path, args.debug)

if __name__ == '__main__':
    main()
