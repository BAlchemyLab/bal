#!/bin/env python

import sys
import time
import bcnode

from mininet.topo import MinimalTopo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host, CPULimitedHost
from mininet.util import specialClass

tests = {
    "btc": [bcnode.BtcNode, 'getwalletinfo'],
    "eth": [bcnode.EthNode, 'admin.nodeInfo'],
    "pow": [bcnode.POWNode, 'chain'],
    "qkd": [bcnode.QNode, 'chain']
    }

test = tests[sys.argv[1]]

net = Mininet( topo=MinimalTopo(), host=test[0])

net.start()

for node in net.hosts:
    node.start()

time.sleep(5)

for node in net.hosts:
    print (node.call(test[1]))

result=CLI(net)

for node in net.hosts:
    node.stop()
net.stop()
