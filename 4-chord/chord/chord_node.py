"""
:file: chord_node.py
:brief: chord_node takes a port number of an existing node (or 0 to indicate it should
start a new network). This program joins a new node into the network using a
system-assigned port number for itself. The node joins and then listens for incoming
connections (other nodes or queriers). You can use blocking TCP for this and pickle for
the marshaling.
"""

import array      # to encode prior to hash
import hashlib    # for consistent hashing with SHA-1
import pickle     # for marshalling and unmarshalling
import socket     # for rpc calls
import string
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
class FingerEntry(object):
    """
    Row in a finger table.

    >>> fe = FingerEntry(0, 1)
    >>> fe

    >>> fe.node_id = 1
    >>> fe

    >>> 1 in fe, 2 in fe
    (True, False)
    >>> FingerEntry(0, 2, 3), FingerEntry(0, 3, 0)
    (, )
    >>> FingerEntry(3, 1, 0), FingerEntry(3, 2, 0), FingerEntry(3, 3, 0)
    (, , )
    >>> fe = FingerEntry(3, 3, 0)
    >>> 7 in fe and 0 in fe and 2 in fe and 3 not in fe
    True
    """

    def __init__(self, n, k, node=None):
        if not (0 <= n < NODES and 0 < k <= M):
            raise ValueError('invalid finger entry values')
        self.start = (n + 2 ** (k - 1)) % NODES
        self.next_start = (n + 2 ** k) % NODES if k < M else n
        self.interval = ModRange(self.start, self.next_start, NODES)
        self.node = node

    def __repr__(self):
        """ Something like the interval|node charts in the paper """
        return ''.format(self.start, self.next_start, self.node)

    def __contains__(self, id):
        """ Is the given id within this finger's interval? """
        return id in self.interval


# chord node class
class ChordNode(object):
    def __init__(self, n):
        global TEST_BASE

        # networking init
        self.port = n
        self.addr = (socket.gethostbyname('localhost'), self.port)

        # node prop init
        self.node_id = self.get_node_hash(n)
        # self.finger = [None] + [FingerEntry(n, k) for k in range(1, M+1)]  # indexing starts at 1
        # self.predecessor = None
        # self.keys = {}

        # threading start TODO TEST THREADING WHEN RPC CALLS DONE
        # listening_thread = threading.Thread(target=self.listen_thread(), args=(self.addr))
        # listening_thread.start()

        # log
        print('chordnod: Created new ChordNode on port {} w/ id {}'.format(self.port,
                                                                         self.node_id))

    ###### start chord algo methods

    @staticmethod
    def get_node_hash(n):
        """ Creates the node id by hashing the endpoint and port using SHA1 per spec.
        :return: hashed node id
        """
        return hashlib.sha1((socket.gethostbyname('localhost') + str(n)).encode()).digest()

    @property
    def successor(self):
        return self.finger[1].node_id

    @successor.setter
    def successor(self, id):
        self.finger[1].node_id = id

    def find_successor(self, id):
        """ Ask this node to find id's successor = successor(predecessor(id))"""
        np = self.find_predecessor(id)
        return self.call_rpc(np, 'successor')

    # TODO
    def find_predecessor(self, id):
        pass

    ###### end chord algo methods

    ###### start networking rpc methods

    # TODO
    def call_rpc(self, np, param):
        pass

    def dispatch_rpc(self, method, arg1, arg2):  # server side
        """

        :param method:
        :param arg1:
        :param arg2:
        :return:
        """

    def handle_rpc(self, client):  # server side
        """Unmarshalls msg from client, routes request to dispatch_rpc, waits
        for result and sends back to client."""
        rpc = client.recv(BUF_SZ)
        method, arg1, arg2 = pickle.loads(rpc)
        result = self.dispatch_rpc(method, arg1, arg2)
        client.sendall(pickle.dumps(result))

    def listen_thread(self):  # server side
        """Starts threaded listening server to handle incoming requests"""

        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        #     server.setblocking(False)
        #     server.bind(self.addr)
        #     server.listen(BACKLOG)
        #     while True:
        #         client, client_addr = server.accept()
        #         threading.Thread(target=self.handle_rpc, args=(client,)).start()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.addr)
        server.listen(BACKLOG)
        while True:
            client, client_addr = server.accept()
            threading.Thread(target=self.handle_rpc, args=(client,)).start()

    ###### end networking rpc methods



if __name__ == '__main__':
    # print('chord_node.py')
    if len(sys.argv) != 2:
        print('Usage to start new node in new network: ')
        print('python chord_node.py 0')

        print('Usage to join new node to existing network: ')
        print('python chord_node.py [port of existing node]')

    port = int(sys.argv[1])  # todo update to endpoint IP + port
    # create new node
    node = ChordNode(port)

    # TODO join existing chord
    # if port != 0:
    #     node.join_chord(port)
    #     print('Joined ChordNode {} to existing chord')

