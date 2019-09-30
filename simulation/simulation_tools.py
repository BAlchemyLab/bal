from mininet.cli import CLI
from mininet.term import makeTerms
from collections import defaultdict
from mininet.node import Host, Switch
import yaml
import os
import itertools
flatten = itertools.chain.from_iterable

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
            bandwith = to_intf.params.get('bw',100)

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

def dump_graph(edge_list, dir_path):
    with open(dir_path + 'graph.txt', 'w') as file:  # Use file to refer to the file object
        file.write(str(edge_list))
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


def send_transaction(from_host, to_host, amount, silent = False):
    to_host_addr = yaml.safe_load(to_host.call('address/my', True))['address']
    transaction_param = '{"recipient": "%s", "amount": %f}' % (to_host_addr, amount)
    from_host.call('transactions/send', silent, transaction_param)

def register_peers(from_host, to_host):
    peer_param = '{"peer": "%s:%s"}' % (to_host.IP(), to_host.socket)
    from_host.call('peers/register', True, peer_param)

def wait_and_forge_transactions(verifier, transaction_number):
    current_transaction_pool = yaml.safe_load(verifier.call('transactions/pool', True))
    while len(current_transaction_pool) < transaction_number:
        sleep(0.5)
        current_transaction_pool = yaml.safe_load(verifier.call('transactions/pool', True))
    verifier.call('block/generate')

def add_host_helper(host_name, ip, switch, net):
    host = net.addHost(host_name, ip=ip, defaultRoute=None)
    link = net.addLink(host, switch)
    switch.attach(link.intf2)
    host.configDefault()
    sleep(2)
    host.start('/tmp/')
    makeTerms([host])
    return host

def verifier_check_amount(host, verifier):
    host_addr = yaml.safe_load(host.call('address/my', True))['address']
    req = 'balance/%s' % (host_addr,)
    return yaml.safe_load(verifier.call(req, True))['balance']

def open_mininet_cli(net):
    print('Opening Mininet CLI before changing current topology (Closing CLI will resume the script)')
    result=CLI(net)
