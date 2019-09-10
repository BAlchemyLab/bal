#!/usr/bin/python
import random
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSBridge, UserSwitch, CPULimitedHost
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink
from mininet.topo import Topo
import networkx as nx
import itertools
import sys
import math

def topo_to_edgelist(topo):
    G = topo.convertTo(nx.MultiGraph)
    edge_list_str = [str(u) + ' ' + str(v) + ' ' + str(bw) for u,v,bw in G.edges(data='bw')]
    return edge_list_str

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
    max_edge = v * (v - 1)/2
    e = max_edge if e > max_edge else e
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

def mininet_topo(switch_number, edge_number, host_number, max_bw):
    switch_matrix = random_connected_graph(switch_number, edge_number)
    net = Topo()
    switches = [None] * switch_number
    for i in range(1, switch_number+1):
        switches[i-1] = net.addSwitch('s' + str(i), failMode = 'standalone', stp=1)

    for i in range(1, host_number+1):
        ran_bw = ran(max_bw)+1
        cpu_f = (ran_bw*1.0 / max_bw)
        host = net.addHost('h'+ str(i), defaultRoute=None, cpu=cpu_f)
        selected_sw = random.choice(switches)
        net.addLink(selected_sw, host, bw=ran_bw)

    for i in range (1, switch_number):
        for j in range(i+1, switch_number+1):
            index = ( i - 1 ) * switch_number + j - 1
            if switch_matrix[ index ]:
                net.addLink(switches[i-1], switches[j-1], bw=max_bw)
    return net

if __name__ == '__main__':
    setLogLevel( 'info' )
    switch_number = int(input("Number of switches:"))
    host_number = int(input("Number of hosts:"))
    edge_number = int(input("Number of minimum links:"))
    max_bw = int(input("Maximum Bandwidth:"))

    print("switch=%d hosts=%d minLinks=%d MaxBW=%d\n" % (switch_number, host_number, edge_number, max_bw))

    topo = mininet_topo(switch_number, edge_number, host_number, max_bw)
    net_params = {'switch': OVSBridge, 'link': TCLink, 'host': CPULimitedHost,
                    'ipBase': '10.0.0.0/8', 'waitConnected' : True, 'topo' : topo,
                    'build': False}
    net = Mininet(**net_params)
    net.build()
    net.start()
    CLI( net )
    net.stop()
