#!/usr/bin/env python

import sys
import yaml
import json

from time import sleep, time
from mininet.topo import SingleSwitchTopo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host, CPULimitedHost, OVSBridge, Switch
from mininet.util import specialClass
from mininet.link import TCLink
from mininet.term import makeTerms
from bal.bcnode import POWNode, POSNode
from bal.BaseBlockchain import BLOCK_GENERATION_INTERVAL
from collections import defaultdict
import random
import itertools
import os
from functools import partial
from mininet.log import setLogLevel
import shutil
import getopt
import traceback
from argparse import ArgumentParser
import networkx as nx
from simulation.bcmn_simulation import *
from simulation.simulation_tools import *
import complex_random_topology_generator as rtg

flatten = itertools.chain.from_iterable

def simulate(host_number, number_of_transactions, root_path):
    timestamp_str = str(int(time()))
    k = 4
    wiring_p = 0.0
    repeat = 5
    for x in range(repeat+1):
        print("Simulating with rewiring probability:" + str(wiring_p))
        G = nx.connected_watts_strogatz_graph(host_number, k ,wiring_p)
        adj_matrix = rtg.nx_graph_to_adj_matrix(G)
        edge_list = rtg.graph_to_str(adj_matrix)
        subsimulation(adj_matrix, host_number, wiring_p, root_path, number_of_transactions, timestamp_str, edge_list)
        wiring_p = wiring_p + 1.0/repeat

def subsimulation(adj_matrix, host_number, wiring_p, root_path, number_of_transactions, timestamp_str, edge_list):
    net = None
    try:
        start_time = time()
        net_params = {'topo': None, 'build': False, 'host': POWNode, 'switch': OVSBridge,
                        'link': TCLink, 'ipBase': '10.0.0.0/8', 'waitConnected' : True, 'xterms': False}
        net = rtg.mininet_topo(adj_matrix, net_params)
        net.build()
        net.start()

        miner_number = 1
        miners = random.sample(net.hosts, miner_number)
        verifier = random.choice(miners)
        parametered_path = 'h' + str(host_number) + 'p' + str(wiring_p)
        ts_dir_path = init_simulation_path(root_path + parametered_path + '/' + timestamp_str + '/')

        for node in net.hosts:
            node.start(ts_dir_path)

        sleep(2) # Wait for nodes to be started completely.

        peer_topology = register_peer_topology(net)

        dump_graph(edge_list, ts_dir_path)
        dump_net(net, peer_topology, miners, ts_dir_path)

        target_amount = 10
        target_number = 3
        random_generator_number = target_number - len(miners) if target_number > len(miners) else 0
        random_generator_hosts = random.sample([x for x in net.hosts if x not in miners], random_generator_number)
        generators = miners + random_generator_hosts

        for node in generators:
            node.call('block/generate/loop/start', True)

        print("Waiting for block generations for initial target amounts.")
        generated = []
        while len(generated) != target_number:
            sleep(BLOCK_GENERATION_INTERVAL)
            print('***** AMOUNT CONTROL *****')
            for h in generators:
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
        while i < number_of_transactions:
            receiver = random.sample([x for x in net.hosts if x not in miners], 1)[0]
            sender = random.sample(miners, 1)[0]
            current_block_number = yaml.safe_load(sender.call('chain/length', True))
            while current_block_number <= temp_block_number:
                sleep(BLOCK_GENERATION_INTERVAL)
                current_block_number = yaml.safe_load(sender.call('chain/length', True))

            if send_and_log_transaction(sender, receiver, 1, ts_dir_path):
                i = i + 1
                sleep(1)
                temp_block_number = yaml.safe_load(sender.call('chain/length', True))

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

def dump_graph(edge_list, dir_path):
    with open(dir_path + 'graph.txt', 'w') as file:  # Use file to refer to the file object
        file.write(str(edge_list))
        file.write('\n')

def register_peer_topology(net):
    print("Registering peers")
    peers_by_switch = []

    switch_map, max_bw_map = get_switch_map(net)

    for switch, values in switch_map.iteritems():
        host_name = values['hosts'].keys()[0]
        host1 = net.getNodeByName(host_name)
        switch_names = values['switches'].keys()
        for sw in switch_names:
            sw_host = switch_map[sw]['hosts'].keys()[0]
            host2 = net.getNodeByName(sw_host)
            register_peers(host1, host2)
            peers_by_switch.extend([(host_name, sw_host)])

    return peers_by_switch

def main():
    host_type = None
    parser = ArgumentParser()
    parser.add_argument('-p', '--path', default='/tmp/', type=str, help='where the logs will be located. default: /tmp/')
    args = parser.parse_args()
    tmp_location = '/tmp/bcn'
    if os.path.exists(tmp_location):
        shutil.rmtree('/tmp/bcn')
    setLogLevel( 'info' )
    host_number = int(input("Number of hosts(>10):"))
    number_of_transactions = int(input("Number of repeated random transactions:"))
    simulate(host_number, number_of_transactions, args.path)

if __name__ == '__main__':
    main()
