"""
:file: chord_node.py
:brief: chord_node takes a port number of an existing node (or 0 to indicate it should
start a new network). This program joins a new node into the network using a
system-assigned port number for itself. The node joins and then listens for incoming
connections (other nodes or queriers). You can use blocking TCP for this and pickle for
the marshaling.
"""

import hashlib    # for consistent hashing with SHA-1
import pickle     # for marshalling and unmarshalling
import socket     # for rpc calls
import sys
import threading  # to prevent deadlock

# globals

M = 3              # TODO: Test size, normally hashlib.sha1().digest_size * 8
NODES = 2**M       # size of the chord, tot num nodes possible
BUF_SZ = 4096      # socket recv arg
BACKLOG = 100      # socket listen arg
TEST_BASE = 43544  # for testing use port numbers on localhost at TEST_BASE + n

# modrange and modrangeiter helper classes

# finger table class

# chord node class


if __name__ == '__main__':
    print('chord_node.py')
    if len(sys.argv) != 2:
        print('Usage to start new node in new network: ')
        print('python chord_node.py 0')

        print('Usage to join new node to existing network: ')
        print('python chord_node.py [port of existing node]')


    port = int(sys.argv[2])  # todo update to endpoint IP + port
    # create new node
    node = ChordNode(port)
    print('Created new ChordNode {}'.format(port))

    # TODO join existing chord
    # if port != 0:
    #     node.join_chord(port)
    #     print('Joined ChordNode {} to existing chord')

