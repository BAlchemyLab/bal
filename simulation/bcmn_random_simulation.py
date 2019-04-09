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
from bcmn_simulation import *


flatten = itertools.chain.from_iterable

def simulate(host_type, host_number, miner_percentage):
    start_time = time()
    timestamp_str = str(int(start_time))
    net_params = {'topo': None, 'build': False, 'host': host_type, 'switch': OVSKernelSwitch,
                    'link': TCLink, 'ipBase': '10.0.0.0/8', 'waitConnected' : True}

    switch_number = host_number / 4
    max_bw = 100

    net = rtg.random_topology(switch_number, host_number, max_bw, net_params)
    net.build()
    net.start()

    verifier = random.choice(net.hosts)
    parametered_path = 'h' + str(host_number) + 'm' + str(miner_percentage)
    ts_dir_path = init_simulation_path('/tmp/' + parametered_path + '/' + timestamp_str + '/')

    for node in net.hosts:
        node.start(ts_dir_path)

    sleep(2) # Wait for nodes to be started completely.

    peer_topology = register_peer_topology(net)

    target_amount = 10
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

    miner_number = len(net.hosts)*miner_percentage / 100
    miners = random.sample(net.hosts, miner_number)

    for miner in miners:
        miner.call('block/generate/loop/start', True)

    sleep(2)
    sender, receiver = random.sample(net.hosts, 2)
    send_and_log_transaction(sender, receiver, 1, ts_dir_path)

    dump_net(net, peer_topology, miners, ts_dir_path)

    while not check_block_txts(ts_dir_path, host_number, 1):
        sleep(0.5)

    sleep(2)

    elapsed_time = time() - start_time
    dump_elapsed_time(elapsed_time, ts_dir_path)
    dump_chain(verifier, ts_dir_path)

def send_and_log_transaction(from_host, to_host, amount, dir_path):
    send_transaction(from_host,to_host,amount)
    with open(dir_path + 'activity.txt', 'a+') as file:  # Use file to refer to the file object
        file.write(from_host.name + ' sends transaction to ' + to_host.name + ' amount: ' + str(amount))
        file.write('\n')

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
    if (not block_txts) or tx_number != len(block_txts):
        return False

    for txt in block_txts:
        count = 0
        with open(dir_path + txt) as f:
            count = len(f.read().split(b'\n')) - 1
        if count != host_number:
            return False
    return True

def main():
    host_type = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],"ht:",["host_type="])
    except getopt.GetoptError:
        print 'bcmn_simulation -ht <POW/POS>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'bcmn_simulation -ht <POW/POS>'
            sys.exit()
        elif opt in ("-ht", "--host_type"):
            if arg == 'POW':
                host_type = POWNode
            elif arg == 'POS':
                host_type = POSNode
            else:
                print 'Unknown host type: ' + arg
                sys.exit()

    if not host_type:
        print 'Specify host with -ht <POW/POS>'
        sys.exit()
    tmp_location = '/tmp/bcn'
    if os.path.exists(tmp_location):
        shutil.rmtree('/tmp/bcn')
    setLogLevel( 'info' )
    host_number = int(input("Number of hosts(>4):"))
    miner_percentage = int(input("Miner percentage (0-100):"))

    simulate(host_type, host_number, miner_percentage)
if __name__ == '__main__':
    main()
