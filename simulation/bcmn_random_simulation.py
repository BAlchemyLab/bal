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
from bcmn_simulation import *


flatten = itertools.chain.from_iterable

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

def send_and_log_transaction(from_host, to_host, amount, dir_path):
    is_tx_creatable = yaml.safe_load(from_host.call('transactions/has_amount/'+str(amount), silent=True))
    if is_tx_creatable:
        send_transaction(from_host,to_host,amount)
        with open(dir_path + 'activity.txt', 'a+') as file:  # Use file to refer to the file object
            file.write(from_host.name + ' sends transaction to ' + to_host.name + ' amount: ' + str(amount))
            file.write('\n')
        return True
    else:
        return False

def get_switch_map(net):
    switch_map = defaultdict(lambda: defaultdict(dict))
    max_bw_map = {}

    for link in net.links:
        from_intf = link.intf1
        switch_name = from_intf.node.name
        to_intf = link.intf2
        if issubclass(type(to_intf.node), Host):
            host_name = to_intf.node.name
            bandwith = to_intf.params['bw']

            temp_val = max([vals for vals in switch_map[switch_name]['hosts'].values()] or [0])
            if temp_val < bandwith:
                max_bw_map[switch_name] = [host_name]

            switch_map[switch_name]['hosts'][host_name] = bandwith
        elif issubclass(type(to_intf.node), Switch):
            switch_map[switch_name]['switches'][to_intf.node.name] = bandwith

    return switch_map, max_bw_map

def register_peer_topology(net):
    print("Registering peers")
    peers_by_switch = []
    peers_by_max_bw = []

    switch_map, max_bw_map = get_switch_map(net)

    for switch, values in switch_map.iteritems():
        host_names = values['hosts'].keys()
        peers_by_switch.extend(list(itertools.combinations(host_names, 2)))
        for pair in itertools.combinations(host_names, 2):
            host1 = net.getNodeByName(pair[0])
            host2 = net.getNodeByName(pair[1])
            register_peers(host1, host2)

    flatten_values = list(flatten(max_bw_map.values()))
    peers_by_max_bw = itertools.combinations(flatten_values, 2)
    for pair in itertools.combinations(flatten_values, 2):
        host1 = net.getNodeByName(pair[0])
        host2 = net.getNodeByName(pair[1])
        register_peers(host1, host2)

    return peers_by_switch + list(peers_by_max_bw)

def dump_chain(host, dir_path):
    with open(dir_path + 'chain.txt', 'w') as file:  # Use file to refer to the file object
        file.write(host.call('chain', True))

def dump_elapsed_time(elapsed_time, dir_path):
    with open(dir_path + 'activity.txt', 'a+') as file:  # Use file to refer to the file object
        file.write('Elapsed time for simulation(in sec):' + str(elapsed_time))
        file.write('\n')

def dump_net(net, peer_topology, miners, dir_path):
    with open(dir_path + 'dump.txt', 'w') as file:  # Use file to refer to the file object
        for node in net.switches + net.hosts:
            file.write(repr(node))
            file.write('\n')

    with open(dir_path + 'links.txt', 'w') as file:  # Use file to refer to the file object
        for node in net.links:
            file.write(str(node))
            file.write('\n')

    with open(dir_path + 'peer_topo.txt', 'w') as file:  # Use file to refer to the file object
        for pair in peer_topology:
            file.write(str(pair))
            file.write('\n')

    with open(dir_path + 'switch_bw_map.txt', 'w') as file:  # Use file to refer to the file object
        for k, v in get_switch_map(net)[0].iteritems():
            file.write(k + ':' + str(dict(v)))
            file.write('\n')

    with open(dir_path + 'miners.txt', 'w') as file:  # Use file to refer to the file object
        for miner in miners:
            file.write(miner.name)
            file.write('\n')

def init_simulation_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def check_block_txts(dir_path, host_number, tx_number):
    block_txts = [filename for filename in os.listdir(dir_path) if filename.startswith("transaction_block")]
    if (not block_txts) or len(block_txts) < tx_number * host_number:
        return False
    return True

def move_txs_to_directories(dir_path):
    move_txs_to_directories_helper(dir_path, "transaction_block")
    move_txs_to_directories_helper(dir_path, "transaction_pool")

def move_txs_to_directories_helper(dir_path, file_prefix):
    filenames = [filename for filename in os.listdir(dir_path) if filename.startswith(file_prefix)]
    new_path = dir_path + file_prefix + '/'
    init_simulation_path(new_path)
    for fname in filenames:
        tx_hash = fname.rsplit('-',2)[1]
        with open(new_path + tx_hash + '.txt' , 'a+') as outfile:
                with open(dir_path + fname) as infile:
                    outfile.write(infile.read())
                os.remove(dir_path + fname)

def main():
    host_type = None
    parser = ArgumentParser()
    parser.add_argument('-ht', '--host_type', default='pow', type=str, help='blockchain consensus class to be used')
    parser.add_argument('-p', '--path', default='/tmp/', type=str, help='where the logs will be located. default: /tmp/')
    parser.add_argument('-d', '--debug', default=False, help='debug mode for xterms.', action='store_true')
    args = parser.parse_args()
    tmp_location = '/tmp/bcn'
    if os.path.exists(tmp_location):
        shutil.rmtree('/tmp/bcn')
    setLogLevel( 'info' )

    if args.host_type.find('pos') == 0:
        host_type = POSNode
    else:
        host_type = POWNode

    host_number = int(input("Number of hosts(>10):"))
    miner_percentage = int(input("Miner percentage (0-100):"))
    number_of_transactions = int(input("Number of repeated random transactions:"))
    number_of_simulations = int(input("Number of repeated simulations:"))
    for i in range(0, number_of_simulations):
        simulate(host_type, host_number, miner_percentage, number_of_transactions, args.path, args.debug)

if __name__ == '__main__':
    main()
