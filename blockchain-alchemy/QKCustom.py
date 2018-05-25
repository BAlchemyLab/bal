from mininet.link import (Link, TCLink, TCULink, OVSLink)
from mininet import util
import time
import subprocess
import os
import atexit

class QKLink(Link):
    @classmethod
    def makeIntfPair(cls, intfname1, intfname2, addr1=None, addr2=None,
                     node1=None, node2=None, deleteIntfs=True):
        """Create pair of interfaces
           intfname1: name for interface 1
           intfname2: name for interface 2
           addr1: MAC address for interface 1 (optional)
           addr2: MAC address for interface 2 (optional)
           node1: home node for interface 1 (optional)
           node2: home node for interface 2 (optional)
           (override this method [and possibly delete()]
           to change link type)"""
        # Leave this as a class method for now
        assert cls
        return makeIntfPair(intfname1, intfname2, addr1, addr2, node1, node2,
                            deleteIntfs)

    def stop(self):
        for p in QKLink.processes:
            p.kill()
        self.delete()


QKLink.processes = []


def makeIntfPair(intf1, intf2, addr1=None, addr2=None, node1=None, node2=None,
                 deleteIntfs=True, runCmd=None):
    """Make a veth pair connnecting new interfaces intf1 and intf2
       intf1: name for interface 1
       intf2: name for interface 2
       addr1: MAC address for interface 1 (optional)
       addr2: MAC address for interface 2 (optional)
       node1: home node for interface 1 (optional)
       node2: home node for interface 2 (optional)
       deleteIntfs: delete intfs before creating them
       runCmd: function to run shell commands (quietRun)
       raises Exception on failure"""
    if not runCmd:
        runCmd = util.quietRun if not node1 else node1.cmd
        runCmd2 = util.quietRun if not node2 else node2.cmd
    if deleteIntfs:
        # Delete any old interfaces with the same names
        runCmd('ip link del ' + intf1)
        runCmd2('ip link del ' + intf2)
    """cmdOutput = util.run('ip tuntap add %s mode tap' %
                         (intf1))
    if cmdOutput:
        raise Exception("Error creating interface pair (%s,%s): %s " %
                        (intf1, intf2, cmdOutput))
    cmdOutput = util.run('ip tuntap add %s mode tap' %
                         (intf2))
    if cmdOutput:
        raise Exception("Error creating interface pair (%s,%s): %s " %
                        (intf1, intf2, cmdOutput))"""
    # Create new pair
    netns = 1 if not node2 else node2.pid
    print('\n/root/qnet/ctapudp/ctapudp -s 0.0.0.0 -p %i -t 127.0.0.1 -k %i -i %s -a 1 -q 127.0.0.1 -r 55554 -e 100\n' % (
        makeIntfPair.portscount, makeIntfPair.portscount + 1, intf1))
    print('\n/root/qnet/ctapudp/ctapudp -s 0.0.0.0 -p %i -t 127.0.0.1 -k %i -i %s -a 1 -q 127.0.0.1 -r 55554 -e 100\n' % (
        makeIntfPair.portscount + 1, makeIntfPair.portscount, intf2))
    process = subprocess.Popen(
        ['/root/qnet/ctapudp/ctapudp', '-s', '127.0.0.1', '-p', str(makeIntfPair.portscount), '-t', '127.0.0.1', '-k',
         str(makeIntfPair.portscount + 1), '-i', intf1, '-a', '1', '-q', '127.0.0.1', '-r', '55554', '-e',
         '100'""", '-d', '1'"""], preexec_fn=os.setpgrp)
    QKLink.processes.append(process)
    process = subprocess.Popen(
        ['/root/qnet/ctapudp/ctapudp', '-s', '127.0.0.1', '-p', str(makeIntfPair.portscount + 1), '-t', '127.0.0.1', '-k',
         str(makeIntfPair.portscount), '-i', intf2, '-a', '1', '-q', '127.0.0.1', '-r', '55554', '-e',
         '100'""", '-d', '1'"""], preexec_fn=os.setpgrp)
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

LINKS = {'default': Link,  # Note: overridden below
         'tc': TCLink,
         'tcu': TCULink,
         'ovs': OVSLink,
         'qk': QKLink}

print('/root/qnet/keyworker/keyworker -n /root/qnet/ctapudp/db1')
process = subprocess.Popen(
    ['/root/qnet/keyworker/keyworker', '-n', '/root/qnet/keyworker/db1','-w','2'""", '-d', '1'"""], preexec_fn=os.setpgrp)


def exit_handler():
    process.kill()

atexit.register(exit_handler)