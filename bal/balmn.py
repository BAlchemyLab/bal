from mininet.node import ( Host, CPULimitedHost )
from mininet.util import specialClass
from mininet.topo import SingleSwitchTopo, LinearTopo, SingleSwitchReversedTopo
from mininet.topolib import TreeTopo
from bal.bcnode import ( POWNode, POSNode )
from bal.MyTopo import MyTopo


HOSTDEF = 'proc'
HOSTS = { 'proc': Host,
          'rt': specialClass( CPULimitedHost, defaults=dict( sched='rt' ) ),
          'cfs': specialClass( CPULimitedHost, defaults=dict( sched='cfs' ) ),
          'pow': POWNode,
          'pos': POSNode}

TOPODEF = 'none'
TOPOS = { 'minimal': lambda: SingleSwitchTopo( k=2 ),
          'linear': LinearTopo,
          'reversed': SingleSwitchReversedTopo,
          'single': SingleSwitchTopo,
          'none': None,
          'tree': TreeTopo
        }
