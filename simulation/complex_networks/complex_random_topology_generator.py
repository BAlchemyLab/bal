#!/usr/bin/python
import random
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, UserSwitch, CPULimitedHost, OVSBridge
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink
import math
import itertools
import sys
#make a class this module
def graph_to_str(adj_matrix):
    str_matrix = []
    v = int(math.sqrt(len(adj_matrix)))
    for i in range (1, v):
        for j in range(i+1, v+1):
            index = ( i - 1 ) * v + j - 1
            if adj_matrix[ index ]:
                str_matrix.append(str(i) + " " + str(j))
    return str_matrix

# Return a random integer between 0 and k-1 inclusive.
def ran( k ):
    return random.randint(0, k-1)

def random_connected_graph(v, e):
    adj_matrix = [0] * v * v
    tree = [0] * v
    init_array(tree, v)
    tree = permute(tree)
    for i in range(1, v):
        j = ran( i )
        adj_matrix[ tree[ i ] * v + tree[ j ] ] = 1
        adj_matrix[ tree[ j ] * v + tree[ i ] ] = 1
    count = v - 1
    while count < e:
        i = ran( v )
        j = ran( v )
        if i == j:
            continue
        if i > j :
            i, j = j, i
        index = i * v + j
        if not adj_matrix[ index ]:
            adj_matrix[ index ] = 1
            count += 1
    return adj_matrix

def permute(arr):
    return random_permutation(arr)

def random_permutation(iterable, r=None):
    "Random selection from itertools.permutations(iterable, r)"
    pool = tuple(iterable)
    r = len(pool) if r is None else r
    return tuple(random.sample(pool, r))

def init_array(arr, end):
   for i in range(0, end):
      arr[i] = i

def mininet_topo(adj_matrix, net_params):
    host_number = int(math.sqrt(len(adj_matrix)))
    net = Mininet(**net_params)
    switches = [None] * host_number
    for i in range(1, host_number+1):
        switches[i-1] = net.addSwitch('s' + str(i), failMode = 'standalone', stp=1)

    for i in range(1, host_number+1):
        host = net.addHost('h'+ str(i), defaultRoute=None)
        selected_sw = switches[i-1]
        net.addLink(selected_sw, host)

    for i in range (1, host_number):
        for j in range(i+1, host_number+1):
            index = ( i - 1 ) * host_number + j - 1
            if adj_matrix[ index ]:
                net.addLink(switches[i-1], switches[j-1])
    return net


if __name__ == '__main__':
    setLogLevel( 'info' )
    host_number = int(input("Number of hosts:"))
    net_params = {'switch': OVSBridge, 'link': TCLink, 'host': CPULimitedHost,
                    'ipBase': '10.0.0.0/8', 'waitConnected' : True}
    edge_number = 2 * host_number
    adj_matrix = random_connected_graph(host_number, edge_number)
    net = mininet_topo(adj_matrix, net_params)
    net.build()
    net.start()
    CLI( net )
    net.stop()
