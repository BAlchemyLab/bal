"""
Block[Chain] Node classes for Mininet.

BCNodes provide a simple abstraction for interacting with Block[Chains]. Local nodes are simply one or more processes on the local machine.
"""

import os

from subprocess import call
from multiprocessing import Process

from mininet.util import quietRun
from mininet.moduledeps import pathCheck

from mininet.cli import CLI
from mininet.node import Host, CPULimitedHost
from mininet.log import info, error, warn, debug

#class BCNode( CPULimitedHost, CLI ):
class BCNode( CPULimitedHost):
    """A BCNode is a Node that is running (or has execed?) an
       block[chain] application."""

    def __init__( self, name, inNamespace=True,
                  server='', sargs='', sdir='/tmp/bcn',
                  client='', cargs='{command}', cdir=None,
                  ip="127.0.0.1", port='', **params ):
        # Server params
        self.server = server
        self.sargs = sargs
        self.sdir = sdir
        # Client params
        self.client = client
        self.cargs = cargs
        self.cdir = cdir

        self.ip = ip
        self.port = port
        CPULimitedHost.__init__( self, name, inNamespace=inNamespace,
                       ip=ip, **params  )

    def start( self ):
        """Start <bcnode> <args> on node.
           Log to /tmp/bc_<name>.log"""
        if self.server:
            pathCheck( self.server )
            cout = '/tmp/bc_' + self.name + '.log'
            if self.sdir is not None:
                try:
                    os.stat(self.sdir)
                except:
                    os.mkdir(self.sdir)
                self.cmd( 'cd ' + self.sdir )
            cmd = self.server
            if self.sargs:
                cmd += " " + self.sargs.format(name=self.name,
                                               IP=self.IP(),
                                               port=self.port,
                                               cdir=self.cdir,
                                               sdir=self.sdir)
            debug( cmd + ' 1>' + cout + ' 2>' + cout + ' &' )
            self.cmd( cmd + ' 1>' + cout + ' 2>' + cout + ' &' )
            self.execed = False

    def stop( self, *args, **kwargs ):
        "Stop node."
        self.cmd( 'kill %' + self.server )
        self.cmd( 'wait %' + self.server )
        super( BCNode, self ).stop( *args, **kwargs )

    def isAvailable( self ):
        "Is executables available?"
        cmd = 'which '
        if self.server:
            cmd += self.server + ' '
        if self.client:
            cmd += self.client
        return quietRun(cmd)


    def call(self, command, data=''):
        """Call <client> <cargs> on node."""
        if self.cdir is not None:
            self.cmd( 'cd ' + self.cdir )
        cmd = self.client
        pathCheck( cmd )

        if self.cargs:
            cmd += " " + self.cargs.format(command=command,
                                           data=data,
                                           name=self.name,
                                           IP=self.IP(),
                                           port=self.port,
                                           cdir=self.cdir,
                                           sdir=self.sdir)
            if data:
                cmd += " " + self.cargs.format(data=data)
        else:
            cmd += " "  + command

        result = self.cmdPrint( cmd )

        debug("command: %s = %s" % (cmd, result))
        return result

class EthNode(BCNode):
    """A EthNode is a BCNode that is running an Geth application."""

    def __init__( self, name, bcclass=None, inNamespace=True,
                  server='geth',
                  sargs='--testnet --syncmode light --cache 1024 --rpc --ws',
                  sdir='/tmp/bcn',
                  client='geth',
                  cargs='--exec {command} --datadir={sdir}/{IP} attach ipc:{sdir}/{IP}/geth.ipc',
                  cdir=None,
                  ip="127.0.0.1", port='', **params ):

        BCNode.__init__( self, name, inNamespace=inNamespace,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, port=port, **params )

    def start( self ):
        """Start <bcnode> <args> on node.
           Log to /tmp/bc_<name>.log"""

        if self.server:
            pathCheck( self.server )
            cout = '/tmp/bc_' + self.name + '.log'
            if self.sdir is not None:
                import os
                self.cmd( 'cd ' + self.sdir )
                sdir = '%s/%s' % (self.sdir, self.IP())
                try:
                    os.stat(sdir)
                except:
                    os.mkdir(sdir)
                self.sargs += ' --datadir=%s --ipcpath %s/geth.ipc' % \
                              (sdir, sdir)
            debug( self.server + ' ' + self.sargs +
                   ' 1>' + cout + ' 2>' + cout + ' &' )
            self.cmd( self.server + ' ' + self.sargs +
                      ' 1>' + cout + ' 2>' + cout + ' &' )
            self.execed = False

class BtcNode(BCNode):
    """A BtcNode is a BCNode that is running an Bitcoin application."""

    def __init__( self, name, bcclass=None, inNamespace=True,
                  server='bitcoind', sargs='-regtest', sdir='/tmp/bcn',
                  client='bitcoin-cli',
                  cargs='-regtest -datadir={sdir}/{IP} {command}',
                  cdir=None,
                  ip="127.0.0.1", port='', **params ):

        BCNode.__init__( self, name, inNamespace=inNamespace,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, port=port, **params )

    def start( self ):
        """Start <bcnode> <args> on node.
           Log to /tmp/bc_<name>.log"""
        if self.server:
            pathCheck( self.server )
            cout = '/tmp/bc_' + self.name + '.log'
            if self.sdir is not None:
                import os
                self.cmd( 'cd ' + self.sdir )
                sdir = '%s/%s' % (self.sdir, self.IP())
                try:
                    os.stat(sdir)
                except:
                    os.mkdir(sdir)
                self.sargs += ' -datadir=' + sdir
            debug( self.server + ' ' + self.sargs +
                   ' 1>' + cout + ' 2>' + cout + ' &' )
            self.cmd( self.server + ' ' + self.sargs +
                      ' 1>' + cout + ' 2>' + cout + ' &' )
            self.execed = False

class POWNode(BCNode):
    """A POWNode is a BCNode that is running an POWBlockchain."""

    def __init__( self, name, bcclass=None, inNamespace=True,
                  server='blockchain.py',
                  sargs='-p {port} -db {sdir}/pow-{IP}.db -k /tmp/{IP}pow.pem',
                  sdir='/tmp/bcn',
                  client='curl',
                  cargs="-s -X GET -H 'Content-Type: application/json' -d '{data}' http://{IP}:{port}/{command}",
                  cdir=None,
                  ip="127.0.0.1", port='5000', **params ):

        BCNode.__init__( self, name, inNamespace=inNamespace,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, port=port, **params )

class POSNode(BCNode):
    """A POSNode is a BCNode that is running an POSBlockchain."""

    def __init__( self, name, bcclass=None, inNamespace=True,
                  server='blockchain.py',
                  sargs='-p {port} -db {sdir}/pos-{IP}.db -v pos -k /tmp/{IP}pos.pem',
                  sdir='/tmp/bcn',
                  client='curl',
                  cargs="-s -X GET -H 'Content-Type: application/json' -d '{data}' http://{IP}:{port}/{command}",
                  cdir=None,
                  ip="127.0.0.1", port='5000', **params ):

        BCNode.__init__( self, name, inNamespace=inNamespace,
                         server=server, sargs=sargs, sdir=sdir,
                         client=client, cargs=cargs, cdir=cdir,
                         ip=ip, port=port, **params )
