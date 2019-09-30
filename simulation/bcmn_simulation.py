#!/usr/bin/env python

import sys

from time import sleep
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch
from bal.bcnode import POWNode, POSNode
import os
from mininet.log import setLogLevel
import shutil
import getopt

def simulate(host_type):
    net = None
    try:
        net = Mininet( topo=None, build=False, host=host_type, ipBase='10.0.0.0/8', xterms=True, waitConnected=True)

        h1 = net.addHost('h1', ip='10.0.0.1', defaultRoute=None)
        h2 = net.addHost('h2', ip='10.0.0.2', defaultRoute=None)
        h3 = net.addHost('h3', ip='10.0.0.3', defaultRoute=None)
        h4 = net.addHost('h4', ip='10.0.0.4', defaultRoute=None)
        verifier = net.addHost('verifier', ip='10.0.1.0', defaultRoute=None)
        s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')
        s2 = net.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')
        net.addLink(s1, h1)
        net.addLink(s1, h2)
        net.addLink(s1, h3)
        net.addLink(s1, h4)
        net.addLink(s1, verifier)
        net.addLink(s2, s1)
        net.build()
        net.start()

        for node in net.hosts:
            node.start('/tmp/')
        sleep(2) # Wait for nodes to be started completely.

        generators = [h1, h2, h3, h4]
        for node in generators:
            register_peers(node, verifier)

        target_amounts = {h1: 12, h2: 20, h3: 35, h4: 45}
        for h, a in target_amounts.iteritems():
            h.call('block/generate/loop/start')

        print("Waiting for block generations for initial target amounts.")
        generated = []
        while len(generated) != len(target_amounts):
            sleep(5)
            print('***** AMOUNT CONTROL *****')
            for h, a in target_amounts.iteritems():
                if h.name in generated:
                    continue
                host_amount = verifier_check_amount(h, verifier)
                print(h.name + ' has ' + str(host_amount) + ' coin currently, target is: ' + str(a))
                if (host_amount >= a):
                    print(h.name + ' has enough coin, stopping generation for it')
                    h.call('block/generate/loop/stop')
                    generated.append(h.name)

        # 6/11/10
        open_mininet_cli(net)
        h5 = add_host_helper('h5', '10.0.0.5', s2, net)
        register_peers(h2, h5)
        register_peers(h3, h5)

        raw_input('Input something to start transactions in 6/11/10: ')
        send_transaction(h2, h5, 20)
        send_transaction(h3, h5, 35)
        wait_and_forge_transactions(verifier, 2)

        #8/11/10 Phase1
        open_mininet_cli(net)
        h6 = add_host_helper('h6', '10.0.0.6', s2, net)
        h7 = add_host_helper('h7', '10.0.0.7', s2, net)
        h8 = add_host_helper('h8', '10.0.0.8', s1, net)
        register_peers(h4, h7)
        register_peers(h4, h8)
        register_peers(h5, h7)
        register_peers(h6, h7)
        register_peers(h5, h6)
        register_peers(h1, h6)

        raw_input('Input something to send transactions in 8/11/10 Phase1: ')
        send_transaction(h1, h6, 12)
        send_transaction(h4, h7, 30)
        send_transaction(h4, h8, 15)
        wait_and_forge_transactions(verifier, 3)

        #8/11/10 between entity
        raw_input('Input something to send mid-transactions(between entity) in 8/11/10')
        send_transaction(h6, h5, 5)
        send_transaction(h7, h5, 30)
        wait_and_forge_transactions(verifier, 2)

        #8/11/10 Phase2
        open_mininet_cli(net)
        h9 = add_host_helper('h9', '10.0.0.9', s1, net)
        h10 = add_host_helper('h10', '10.0.0.10', s1, net)
        register_peers(h6, h9)
        register_peers(h5, h10)

        raw_input('Input something to send transactions in 8/11/10 Phase2: ')
        send_transaction(h6, h9, 7)
        send_transaction(h5, h10, 90)
        wait_and_forge_transactions(verifier, 2)

        #8/11/10 Phase3
        raw_input('Input something to send transactions in 8/11/10 Phase3: ')
        send_transaction(h10, verifier, 90)
        wait_and_forge_transactions(verifier, 1)

        #15/06/2011
        open_mininet_cli(net)
        h11 = add_host_helper('h11', '10.0.0.11', s1, net)
        register_peers(h8, h11)

        raw_input('Input something to send transactions in 15/06/2011: ')
        send_transaction(h8, h11, 15)
        wait_and_forge_transactions(verifier, 1)

        #17/06/2011: Phase1
        open_mininet_cli(net)
        h12 = add_host_helper('h12', '10.0.0.12', s1, net)
        register_peers(h11, h12)

        raw_input('Input something to send transactions in 17/06/2011: Phase1: ')
        target_amount = 12
        transaction_count = 8
        print("Sending " + str(transaction_count) + " number of transactions from h11 to h12")
        for i in range(1, transaction_count + 1):
            send_transaction(h11, h12, target_amount/float(transaction_count), True)
            wait_and_forge_transactions(verifier, 1)
            sleep(0.5)

        #17/06/2011: Phase2
        raw_input('Input something to send transactions in 17/06/2011 Phase2: ')
        send_transaction(h12, verifier, 12)
        wait_and_forge_transactions(verifier, 1)

    finally:
        result=CLI(net)
        net.stop()

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
            if arg == 'pow':
                host_type = POWNode
            elif arg == 'pos':
                host_type = POSNode
            else:
                print 'Unknown host type: ' + arg
                sys.exit()
        print 'Host Type is "', host_type
    if not host_type:
        print 'Specify host with -ht <POW/POS>'
        sys.exit()
    tmp_location = '/tmp/bcn'
    if os.path.exists(tmp_location):
        shutil.rmtree('/tmp/bcn')
    setLogLevel( 'info' )
    simulate(host_type)

if __name__ == '__main__':
    main()
