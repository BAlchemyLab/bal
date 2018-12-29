from mininet.topo import Topo
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf

class MyTopo( Topo ):

    def __init__( self ):
        Topo.__init__( self )
        s7 = self.addSwitch('s7', cls=OVSKernelSwitch, failMode='standalone')
        s10 = self.addSwitch('s10', cls=OVSKernelSwitch, failMode='standalone')
        s9 = self.addSwitch('s9', cls=OVSKernelSwitch, failMode='standalone')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, failMode='standalone')
        s6 = self.addSwitch('s6', cls=OVSKernelSwitch, failMode='standalone')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, failMode='standalone')
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, failMode='standalone')
        s5 = self.addSwitch('s5', cls=OVSKernelSwitch, failMode='standalone')

        info( '*** Add hosts\n')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
        h8 = self.addHost('h8', cls=Host, ip='10.0.0.8', defaultRoute=None)
        h10 = self.addHost('h10', cls=Host, ip='10.0.0.10', defaultRoute=None)
        h6 = self.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None)
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)
        h5 = self.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None)
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
        h9 = self.addHost('h9', cls=Host, ip='10.0.0.9', defaultRoute=None)
        h7 = self.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None)
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)

        info( '*** Add links\n')
        self.addLink(h7, s9)
        self.addLink(s9, h6)
        self.addLink(h4, s10)
        self.addLink(s10, h5)
        self.addLink(h5, s5)
        self.addLink(s5, h8)
        self.addLink(h8, s6)
        self.addLink(s6, h9)
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(h4, s4)
        self.addLink(s1, h7)
        self.addLink(s2, h7)
        self.addLink(s3, h7)
        self.addLink(s4, h7)
        self.addLink(h7, s7)
        self.addLink(s7, h10)
