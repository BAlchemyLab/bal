from mininet.node import ( Host, CPULimitedHost )
from mininet.util import specialClass
from mininet.topo import SingleSwitchTopo, LinearTopo, SingleSwitchReversedTopo
from mininet.topolib import TreeTopo
from bal.bcnode import ( EthNode, BtcNode, POWNode, POSNode )


HOSTDEF = 'proc'
HOSTS = { 'proc': Host,
          'rt': specialClass( CPULimitedHost, defaults=dict( sched='rt' ) ),
          'cfs': specialClass( CPULimitedHost, defaults=dict( sched='cfs' ) ),
          'pow': POWNode,
          'btc': BtcNode,
          'eth': EthNode,
          'pos': POSNode}

TOPODEF = 'none'
TOPOS = { 'minimal': lambda: SingleSwitchTopo( k=2 ),
          'linear': LinearTopo,
          'reversed': SingleSwitchReversedTopo,
          'single': SingleSwitchTopo,
          'none': None,
          'tree': TreeTopo }
