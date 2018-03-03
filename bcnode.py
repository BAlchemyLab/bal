"""
Block[Chain] Node classes for Mininet.

BCNodes provide a simple abstraction for interacting with Block[Chains]. Local nodes are simply one or more processes on the local machine.
"""

import os
from subprocess import call
from multiprocessing import Process

from mininet.util import quietRun
from mininet.log import info, error, warn, debug
from mininet.moduledeps import pathCheck

from mininet.node import Node 

class BCNode( Node ):
    """A BCNode is a Node that is running (or has execed?) an
       block[chain] application."""

    def __init__( self, name, inNamespace=False,
                  server='', sargs='', sdir=None,
                  client='bash', cargs='', cdir=None,
                  ip="127.0.0.1", **params ):
        # Server params
        self.server = server
        self.sargs = sargs
        self.sdir = sdir
        # Client params
        self.client = client
        self.cargs = cargs
        self.cdir = cdir

        self.ip = ip
        Node.__init__( self, name, inNamespace=inNamespace,
                       ip=ip, **params  )

    def start( self ):
        """Start <bcnode> <args> on node.
           Log to /tmp/bc_<name>.log"""
        if self.server:
            pathCheck( self.server )
            cout = '/tmp/bc_' + self.name + '.log'
            if self.sdir is not None:
                self.cmd( 'cd ' + self.sdir )
            print( self.server + ' ' + self.sargs +
                   ' 1>' + cout + ' 2>' + cout + ' &' )
            self.cmd( self.server + ' ' + self.sargs +
                      ' 1>' + cout + ' 2>' + cout + ' &' )
            self.execed = False

    def stop( self, *args, **kwargs ):
        "Stop node."
        self.cmd( 'kill %' + self.server )
        self.cmd( 'wait %' + self.server )
        super( BCNode, self ).stop( *args, **kwargs )

    def IP( self, intf=None ):
        "Return IP address of the BCNode"
        if self.intfs:
            ip = Node.IP( self, intf )
        else:
            ip = self.ip
        return ip

    def __repr__( self ):
        "More informative string representation"
        return '<%s %s: %s pid=%s> ' % (
            self.__class__.__name__, self.name,
            self.IP(), self.pid )

    def isAvailable( self ):
        "Is executables available?"
        cmd = 'which '
        if self.server:
            cmd += self.server + ' '
        if self.client:
            cmd += self.client
        return quietRun(cmd)

    def CLI(self):
        """Start <bcnode> <args> on node.
           Log to /tmp/bcN.log"""
        pathCheck( self.client )
        if self.cdir is not None:
            self.cmd( 'cd ' + self.cdir )
        print(self.client + " " + self.cargs)
        call( self.client + " " + self.cargs, shell=True )

        

class EthNode(BCNode):
    """A EthNode is a BCNode that is running an Geth application."""

    def __init__( self, name, bcclass=None, inNamespace=False,
                  server='geth',
                  sargs='--testnet --syncmode light --cache 1024 ' +
                  '--ipcpath ~/.ethereum/geth.ipc --rpc --ws',
                  sdir=None,
                  client='geth',
                  cargs='attach ipc:' + os.environ['HOME'] +
                  '/.ethereum/geth.ipc',
                  cdir=None,
                  ip="127.0.0.1", **params ):

        BCNode.__init__( self, name,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, **params )

class BtcNode(BCNode):
    """A BtcNode is a BCNode that is running an Bitcoin application."""

    def __init__( self, name, bcclass=None, inNamespace=False,
                  server='bitcoind', sargs='-regtest', sdir=None,
                  client='bash', cargs='', cdir=None,
                  ip="127.0.0.1", **params ):

        BCNode.__init__( self, name,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, **params )

class POWNode(BCNode):
    """A POWNode is a BCNode that is running an POWBlockChain."""

    def __init__( self, name, bcclass=None, inNamespace=False,
                  server='', sargs={'host':'0.0.0.0','port':5000,
                                    'difficulty':4, 'db':'pow.db'},
                  sdir=None,
                  client='bash', cargs='', cdir=None,
                  ip="127.0.0.1", **params ):

        BCNode.__init__( self, name,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, **params )

    def app(self):
        from POWBlockChain import POWBlockChain
        import blockchain

        args = self.sargs
        blockchain.blockchain = POWBlockChain(difficulty=args['difficulty'])
        if args['db']:
            blockchain.blockchain.init_db(args['db'])
        blockchain.app.run(host=args['host'], port=args['port'], threaded=True)

    def start( self ):
        """Start <pownode> <args> on node."""
        if self.server:
            BCNode.start(self)
        else:
            self.server_process = Process(target=self.app)
            self.server_process.start()

    def stop( self, *args, **kwargs ):
         self.server_process.terminate()
         super( BCNode, self ).stop( *args, **kwargs )

class QNode(BCNode):
    """A QNode is a BCNode that is running an QuantumBlockChain application."""

    def __init__( self, name, bcclass=None, inNamespace=False,
                  server='', sargs={'host':'0.0.0.0','port':5000,
                                    'db':'quant.db'},
                  sdir=None,
                  client='bash', cargs='', cdir=None,
                  keyworker='keyworker', kargs='-d 1', kdir=None,
                  qkdemu='qkdemu', eargs='http://localhost:55554', edir=None,
                  ip="127.0.0.1", **params ):

        # Keyworker params
        self.keyworker = keyworker
        self.kargs = kargs
        self.kdir = kdir

        # QKD emulator params
        self.qkdemu = qkdemu
        self.eargs = eargs
        self.edir = edir

        BCNode.__init__( self, name,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, **params )

    def app(self):
        from QuantumBlockChain import QuantumBlockChain
        import blockchain

        args = self.sargs
        blockchain.blockchain = QuantumBlockChain(blockchain.app)
        if args['db']:
            blockchain.blockchain.init_db(args['db'])
        blockchain.app.run(host=args['host'], port=args['port'], threaded=True)

    def start( self ):
        """Start <qnode> <sargs> on node."""
        if self.server:
            BCNode.start(self)
        else:
            self.server_process = Process(target=self.app)
            self.server_process.start()

    def stop( self, *args, **kwargs ):
         self.server_process.terminate()
         super( BCNode, self ).stop( *args, **kwargs )

    def kwstart( self ):
        """Start keyworker on node.
           Log to /tmp/kw_<name>.log"""
        if self.keyworker:
            pathCheck( self.keyworker )
            cout = '/tmp/kw_' + self.name + '.log'
            if self.kdir is not None:
                self.cmd( 'cd ' + self.kdir )
            print( self.keyworker + ' ' + self.kargs +
                   ' 1>' + cout + ' 2>' + cout + ' &' )
            self.cmd( self.keyworker + ' ' + self.kargs +
                      ' 1>' + cout + ' 2>' + cout + ' &' )
            self.kexeced = False

    def kwstop( self, *args, **kwargs ):
        "Stop keyworker."
        self.cmd( 'kill %' + self.keyworker )
        self.cmd( 'wait %' + self.keyworker )
        super( BCNode, self ).stop( *args, **kwargs )

    def qkey( self ):
        """Send emulated quantum key to keyworker.
           Log to /tmp/kqd_<name>.log"""
        if self.edir is not None:
            self.cmd( 'cd ' + self.edir )
        cout = '/tmp/kqd_' + self.name + '.log'
        self.cmd( self.qkdemu + ' ' + self.eargs +
                  ' 1>' + cout + ' 2>' + cout )
