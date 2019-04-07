#!/usr/bin/python
import random
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, UserSwitch, CPULimitedHost
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink
import itertools
import sys
#make a class this module
def graph_to_str(v, adj_matrix):
    str_matrix = []
    for i in range (1, v):
        for j in range(i+1, v+1):
            index = ( i - 1 ) * v + j - 1
            if adj_matrix[ index ]:
                str_matrix.append(str(i) + " " + str(j) + " " + str(adj_matrix[index]))
    return str_matrix

# Return a random integer between 0 and k-1 inclusive.
def ran( k ):
    return random.randint(0, k-1)

def random_connected_graph(v, e, w):
    adj_matrix = [0] * v * v
    tree = [0] * v
    init_array(tree, v)
    tree = permute(tree)

    for i in range(1, v):
        j = ran( i )
        adj_matrix[ tree[ i ] * v + tree[ j ] ] = ran(w) + 1
        adj_matrix[ tree[ j ] * v + tree[ i ] ] = ran(w) + 1

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
            adj_matrix[ index ] = ran(w) + 1
            count += 1

    return adj_matrix

def permute(arr):
    perm_list = list(itertools.permutations(arr))
    return random.choice(perm_list)

def init_array(arr, end):
   for i in range(0, end):
      arr[i] = i

def random_topology(switch_number, host_number, max_bw, net_params):
    link_number = ran(switch_number * (switch_number-1)/2)

    adj_matrix = random_connected_graph(switch_number, link_number, max_bw)

    net = Mininet(**net_params)
    switches = [None] * switch_number
    for i in range(0, switch_number):
      switches[i] = net.addSwitch('s' + str(i + 1), failMode = 'standalone')

    for i in range(0, host_number):
        host = net.addHost('h'+ str(i + 1), defaultRoute=None)
        selected_sw = random.choice(switches)
        ran_bw = ran(max_bw)+1
        net.addLink(selected_sw, host, bw=ran_bw)

    for i in range (1, switch_number):
        for j in range(i+1, switch_number+1):
            index = ( i - 1 ) * switch_number + j - 1
            if adj_matrix[ index ]:
                net.addLink(switches[i-1], switches[j-1], bw=adj_matrix[index])
    return net


if __name__ == '__main__':
    setLogLevel( 'info' )
    n = int(input("Number of switches:"))
    h = int(input("Number of hosts:"))

    max_bw = int(input("Maximum Bandwidth:"))
    print("N=%d H=%d MaxBW=%d\n" % (n, h, max_bw))
    net_params = {'switch': OVSKernelSwitch, 'link': TCLink, 'host': CPULimitedHost,
                    'ipBase': '10.0.0.0/8', 'waitConnected' : True}
    net = random_topology(n, h, max_bw, net_params)
    net.build()
    CLI( net )
    net.stop()
