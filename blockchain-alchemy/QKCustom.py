from mininet.link import (Link, TCLink, TCULink, OVSLink)
from mininet import util


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
        print("\n!!1!!\n")
        return makeIntfPair(intfname1, intfname2, addr1, addr2, node1, node2,
                            deleteIntfs=deleteIntfs)

def makeIntfPair( intf1, intf2, addr1=None, addr2=None, node1=None, node2=None,
                  deleteIntfs=True, runCmd=None ):
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
        runCmd( 'ip link del ' + intf1 )
        runCmd2( 'ip link del ' + intf2 )
    # Create new pair
    netns = 1 if not node2 else node2.pid
    if addr1 is None and addr2 is None:
        cmdOutput = runCmd( 'ip link add name %s '
                            'type veth peer name %s '
                            'netns %s' % ( intf1, intf2, netns ) )
    else:
        cmdOutput = runCmd( 'ip link add name %s '
                            'address %s '
                            'type veth peer name %s '
                            'address %s '
                            'netns %s' %
                            (  intf1, addr1, intf2, addr2, netns ) )
    if cmdOutput:
        raise Exception( "Error creating interface pair (%s,%s): %s " %
                         ( intf1, intf2, cmdOutput ) )


LINKS = {'default': Link,  # Note: overridden below
         'tc': TCLink,
         'tcu': TCULink,
         'ovs': OVSLink,
         'qk': QKLink}
