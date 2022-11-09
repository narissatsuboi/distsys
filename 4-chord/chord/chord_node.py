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
class ModRange(object):
    """
    Range-like object that wraps around 0 at some divisor using modulo arithmetic.

    >>> mr = ModRange(1, 4, 100)
    >>> mr
    <mrange [1,4)%100>
    >>> 1 in mr and 2 in mr and 4 not in mr
    True
    >>> [i for i in mr]
    [1, 2, 3]
    >>> mr = ModRange(97, 2, 100)
    >>> 0 in mr and 99 in mr and 2 not in mr and 97 in mr
    True
    >>> [i for i in mr]
    [97, 98, 99, 0, 1]
    >>> [i for i in ModRange(0, 0, 5)]
    [0, 1, 2, 3, 4]
    """

    def __init__(self, start, stop, divisor):
        self.divisor = divisor
        self.start = start % self.divisor
        self.stop = stop % self.divisor
        # we want to use ranges to make things speedy, but if it wraps around the 0 node, we have to use two
        if self.start < self.stop:
            self.intervals = (range(self.start, self.stop),)
        elif self.stop == 0:
            self.intervals = (range(self.start, self.divisor),)
        else:
            self.intervals = (range(self.start, self.divisor), range(0, self.stop))

    def __repr__(self):
        """ Something like the interval|node charts in the paper """
        return ''.format(self.start, self.stop, self.divisor)

    def __contains__(self, id):
        """ Is the given id within this finger's interval? """
        for interval in self.intervals:
            if id in interval:
                return True
        return False

    def __len__(self):
        total = 0
        for interval in self.intervals:
            total += len(interval)
        return total

    def __iter__(self):
        return ModRangeIter(self, 0, -1)


class ModRangeIter(object):
    """ Iterator class for ModRange """
    def __init__(self, mr, i, j):
        self.mr, self.i, self.j = mr, i, j

    def __iter__(self):
        return ModRangeIter(self.mr, self.i, self.j)

    def __next__(self):
        if self.j == len(self.mr.intervals[self.i]) - 1:
            if self.i == len(self.mr.intervals) - 1:
                raise StopIteration()
            else:
                self.i += 1
                self.j = 0
        else:
            self.j += 1
        return self.mr.intervals[self.i][self.j]
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

