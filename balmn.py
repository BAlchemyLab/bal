from mininet.node import ( Host, CPULimitedHost )
from bal.bcnode import ( EthNode, BtcNode, POWNode, QNode )
from mininet.util import specialClass

HOSTDEF = 'proc'
HOSTS = { 'proc': Host,
          'rt': specialClass( CPULimitedHost, defaults=dict( sched='rt' ) ),
          'cfs': specialClass( CPULimitedHost, defaults=dict( sched='cfs' ) ),
          'quant': QNode,
          'pow': POWNode,
          'btc': BtcNode,
          'eth': EthNode}
