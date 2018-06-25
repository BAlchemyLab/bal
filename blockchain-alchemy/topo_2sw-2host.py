from mininet.topo import Topo
from mininet.link import Link
from mininet.link import TCIntf
from mininet import util
from mininet.node import OVSSwitch
import time
import subprocess
import os
import atexit


class QKLink(Link):
    @classmethod
    def makeIntfPair(cls, intfname1, intfname2, addr1=None, addr2=None,
                     node1=None, node2=None, deleteIntfs=True):
        assert cls
        print('QKlink')
        return makeIntfPair(intfname1, intfname2, addr1, addr2, node1, node2,
                            deleteIntfs, isEncrypted=True)

    def stop(self):
        for p in QKLink.processes:
            p.kill()
        self.delete()

class QKLinkRaw(Link):
    @classmethod
    def makeIntfPair(cls, intfname1, intfname2, addr1=None, addr2=None,
                     node1=None, node2=None, deleteIntfs=True):
        assert cls
        print('QKlinkRaw')
        return makeIntfPair(intfname1, intfname2, addr1, addr2, node1, node2,
                            deleteIntfs, isEncrypted=False)

    def stop(self):
        for p in QKLink.processes:
            p.kill()
        self.delete()


QKLink.processes = []


def makeIntfPair(intf1, intf2, addr1=None, addr2=None, node1=None, node2=None,
                 deleteIntfs=True, runCmd=None, isEncrypted=True):
    if not runCmd:
        runCmd = util.quietRun if not node1 else node1.cmd
        runCmd2 = util.quietRun if not node2 else node2.cmd
    if deleteIntfs:
        # Delete any old interfaces with the same names
        runCmd('ip link del ' + intf1)
        runCmd2('ip link del ' + intf2)

    # Create new pair
    netns = 1 if not node2 else node2.pid
    addEnc = '-e 100'
    if isEncrypted == False:
        addEnc = ''
    print(
                '\n/root/qnet/ctapudp/ctapudp -s 0.0.0.0 -p %i -t 127.0.0.1 -k %i -i %s -a 1 -q 127.0.0.1 -r 55554 %s\n' % (
            makeIntfPair.portscount, makeIntfPair.portscount + 1, intf1, addEnc))
    print(
                '\n/root/qnet/ctapudp/ctapudp -s 0.0.0.0 -p %i -t 127.0.0.1 -k %i -i %s -a 1 -q 127.0.0.1 -r 55554 %s\n' % (
            makeIntfPair.portscount + 1, makeIntfPair.portscount, intf2, addEnc))
    if isEncrypted == True:
        process = subprocess.Popen(
            ['/root/qnet/ctapudp/ctapudp', '-s', '127.0.0.1', '-p', str(makeIntfPair.portscount), '-t', '127.0.0.1',
             '-k',
             str(makeIntfPair.portscount + 1), '-i', intf1, '-a', '1', '-q', '127.0.0.1', '-r', '55554', '-e',
             '100'""", '-d', '1'"""], preexec_fn=os.setpgrp)
    else:
        process = subprocess.Popen(
            ['/root/qnet/ctapudp/ctapudp', '-s', '127.0.0.1', '-p', str(makeIntfPair.portscount), '-t', '127.0.0.1',
             '-k',
             str(makeIntfPair.portscount + 1), '-i', intf1, '-a', '1', '-q', '127.0.0.1', '-r', '55554'
             """, '-d', '1'"""], preexec_fn=os.setpgrp)
    QKLink.processes.append(process)
    if isEncrypted == True:
        process = subprocess.Popen(
            ['/root/qnet/ctapudp/ctapudp', '-s', '127.0.0.1', '-p', str(makeIntfPair.portscount + 1), '-t', '127.0.0.1',
             '-k',
             str(makeIntfPair.portscount), '-i', intf2, '-a', '1', '-q', '127.0.0.1', '-r', '55554', '-e',
             '100'""", '-d', '1'"""], preexec_fn=os.setpgrp)
    else:
        process = subprocess.Popen(
            ['/root/qnet/ctapudp/ctapudp', '-s', '127.0.0.1', '-p', str(makeIntfPair.portscount + 1), '-t', '127.0.0.1',
             '-k',
             str(makeIntfPair.portscount), '-i', intf2, '-a', '1', '-q', '127.0.0.1', '-r', '55554'
             """, '-d', '1'"""], preexec_fn=os.setpgrp)
    QKLink.processes.append(process)
    time.sleep(0.5)
    makeIntfPair.portscount = makeIntfPair.portscount + 2
    if addr1 is None:
        cmdOutput = util.run('ip link set %s '
                             'netns %s' %
                             (intf1, node1.pid))
    else:
        cmdOutput = util.run('ip link set %s address %s '
                             'netns %s' %
                             (intf1, addr1, node1.pid))

    if cmdOutput:
        for p in QKLink.processes:
            p.kill()
        raise Exception("Error creating interface pair (%s,%s): %s " %
                        (intf1, intf2, cmdOutput))
    if addr2 is None:
        cmdOutput = util.run('ip link set %s '
                             'netns %s' %
                             (intf2, netns))
    else:
        cmdOutput = util.run('ip link set %s address %s '
                             'netns %s' %
                             (intf2, addr2, netns))

    if cmdOutput:
        for p in QKLink.processes:
            p.kill()
        raise Exception("Error creating interface pair (%s,%s): %s " %
                        (intf1, intf2, cmdOutput))


makeIntfPair.portscount = 3333


class MyTopo(Topo):
    "2 switch 2 host custom topology"

    def __init__(self):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        leftHost = self.addHost('h1')
        rightHost = self.addHost('h2')
        leftSwitch = self.addSwitch('s1', cls = OVSSwitch, protocols='OpenFlow13', dpid='000016ccbbe0d642')
        rightSwitch = self.addSwitch('s2', cls = OVSSwitch, protocols='OpenFlow13', dpid='00001ad87e868d45')
        # Add links
        self.addLink(leftHost, leftSwitch, cls=QKLink)
        self.addLink(rightHost, rightSwitch, cls=QKLink)
        self.addLink(leftSwitch, rightSwitch, cls=QKLinkRaw)
        self.addLink(leftSwitch, rightSwitch, cls=QKLink)

process = subprocess.Popen(
    ['/root/qnet/keyworker/keyworker', '-n', '/root/qnet/keyworker/db1', '-w', '2'""", '-d', '1'"""],
    preexec_fn=os.setpgrp)


def exit_handler():
    process.kill()


atexit.register(exit_handler)
topos = {'mytopo': (lambda: MyTopo())}
