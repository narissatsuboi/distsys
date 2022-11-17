"""
:file: chord_node.py
:brief: chord_node takes a port number of an existing node (or 0 to indicate it should
start a new network). This program joins a new node into the network using a
system-assigned port number for itself. The node joins and then listens for incoming
connections (other nodes or queriers). You can use blocking TCP for this and pickle for
the marshaling.
"""

import hashlib  # for consistent hashing with SHA-1
import pickle  # for marshalling and unmarshalling
import socket  # for rpc calls
import sys
import threading  # to prevent deadlock
from datetime import datetime  # for logging

# globals

M = 4  # TODO: Test size, normally hashlib.sha1().digest_size * 8
NODES = 2 ** M  # size of the chord, tot num nodes possible
BUF_SZ = 4096  # socket recv arg
BACKLOG = 100  # socket listen arg
TEST_BASE = 43543  # for testing use port numbers on localhost at TEST_BASE + n
FIRST_NODE_TIMEOUT = 10  # sec
POSSIBLE_HOSTS = ['127.0.01']
POSSIBLE_PORTS = [43543, 43544, 43545, 43546]


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


class FingerEntry(object):
    """
    Row in a finger table.

    >>> fe = FingerEntry(0, 1)
    >>> fe

    >>> fe.node = 1
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
        return '{} {} {}'.format(self.start, self.interval, self.node)

    def __contains__(self, id):
        """ Is the given id within this finger's interval? """
        return id in self.interval


class ChordNode(object):
    global M, NODES

    def __init__(self, n):
        # easy access node info
        self.port = n
        self.addr = ('127.0.0.1', n)
        self.node = self.hash_node(*self.addr)
        self.node_map = self.create_reverse_lookup()
        self.pr_log('__init__ populated lookup table')

        # init finger table, idx starts at 1
        self.finger = [[None], [FingerEntry(self.node, k, self.node) for k in range(1,
                                                                                    M + 1)]]
        self.pr_log('__init__ finger table')
        self.predecessor = None
        self.keys = ()

    def __repr__(self):
        node = 'NODE ' + str(self.node) + ' at ' + str(self.addr) + '\n'
        node += 'KEYS: {}'.format(self.keys) + '\n'
        node += 'PRE : {}'.format(self.predecessor) + '\n'
        # node += 'SUC : {}'.format(self.successor) + '\n'
        node += str(self.finger)
        ft = ''
        ft += ': k  : start :  int  : succ :\n'
        for i in range(1, len(self.finger)):
            ft += ': ' + str(i) + ' :'
            fte = self.finger[i]

        return node + ft

    def pr_log(self, msg):
        """Logs node activities"""
        log = '>>> {} : id {} | {}'.format(self.addr, self.node, msg)
        print(log)

    @staticmethod
    def hash_node(host, port):
        """ Creates the node id by hashing the endpoint and port using SHA1 per spec.
        :return: hashed node id
        """
        addr = str(host) + str(port)
        digest = hashlib.sha1(addr.encode()).hexdigest()
        digest = int(digest, 16) % pow(2, M)
        return digest

    """ BEGIN REVERSE LOOK UP """
    def create_reverse_lookup(self):
        # generate precomputed map {node_ids : addr ...}
        nm = {}
        for host in POSSIBLE_HOSTS:
            host = host
            for port in POSSIBLE_PORTS:
                addr = (host, port)
                n = ChordNode.hash_node(host, port)
                if n in nm:
                    print('cannot use', addr, 'hash conflict', n)
                else:
                    nm[n] = addr
        self.node_map = nm

    def get_node_address(self, hashed_node):
        if hashed_node not in self.node_map:
            print('get_node_address: invalid key')
            return
        return self.node_map[hashed_node]
    """ END REVERSE LOOK UP """

    @property
    def successor(self):
        return self.finger[1].node

    @successor.setter
    def successor(self, id):
        self.finger[1].node = id

    def find_successor(self, id):
        """ Ask this node to find id's successor = successor(predecessor(id))"""
        np = self.find_predecessor(id)
        return self.call_rpc(np, 'successor')

    # TODO
    def find_predecessor(self, id):
        pass

    def update_others(self):
        """ Update all other node that should have this node in their finger tables """
        # print('update_others()')
        for i in range(1, M + 1):  # find last node p whose i-th finger might be this node
            # FIXME: bug in paper, have to add the 1 +
            p = self.find_predecessor((1 + self.node - 2 ** (i - 1) + NODES) % NODES)
            self.call_rpc(p, 'update_finger_table', self.node, i)

    def update_finger_table(self, s, i):
        """ if s is i-th finger of n, update this node's finger table with s """
        # FIXME: don't want e.g. [1, 1) which is the whole circle
        if (self.finger[i].start != self.finger[i].node
                # FIXME: bug in paper, [.start
                and s in ModRange(self.finger[i].start, self.finger[i].node, NODES)):
            print('update_finger_table({},{}): {}[{}] = {} since {} in [{},{})'.format(
                s, i, self.node, i, s, s, self.finger[i].start, self.finger[i].node))
            self.finger[i].node = s
            print('#', self)
            p = self.predecessor  # get first node preceding myself
            self.call_rpc(p, 'update_finger_table', s, i)
            return str(self)
        else:
            return 'did nothing {}'.format(self)

    ###### end chord algo methods

    ###### start networking rpc methods

    def query_handler(self):  # TODO chord_query
        """ a querier to talk to any arbitrary node in the network to query a value for a
        given key or add a key/value pair (with replacement)"""

    def listen_for_key_seed(self):
        """ Each node will wait for FIRST_NODE_TIMEOUT seconds to be populated with all
        the chord's keys (from chord_populate.py). Per the spec, chord_populate.py
        is provided the 1st node's address at the command line, then connects and sends
        all keys in its datastore.

        The first node will save the keys to its keys attribute.

        If this node is NOT the first node or chord_populate.py is down, the timeout will
        return out of this function.
        """
        self.pr_log('waiting to be seeded with keys...')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(FIRST_NODE_TIMEOUT)
            try:
                s.bind(self.addr)
                s.listen(1)
                conn, _addr = s.accept()
            except TimeoutError:
                self.pr_log('not the first node or chord_populate is down')
                return
            else:
                with conn:
                    self.pr_log('chord_populate connected from {}'.format(_addr))
                    data = pickle.loads(conn.recv(BUF_SZ))
                    self.pr_log('keys: {}'.format(data))

                    # store data to keys
                    self.keys.add(data)

    def listen_thread(self):  # server side
        """Starts threaded listening server to handle incoming requests"""

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.addr)
        server.listen(BACKLOG)
        while True:
            client, client_addr = server.accept()
            self.pr_log('listen_thread accepted conn from {}'.format(client_addr))
            threading.Thread(target=self.handle_rpc, args=(client,)).start()

    def handle_rpc(self, client):
        """Unmarshalls msg from client, routes request to dispatch_rpc, waits
        for result and sends back to client."""
        rpc = client.recv(BUF_SZ)
        method, arg1, arg2 = pickle.loads(rpc)
        result = self.rpc_dispatch(method, arg1, arg2)
        client.sendall(pickle.dumps(result))

    # TODO
    def call_rpc(self, np, param):
        pass

    def rpc_dispatch(self, method, arg1, arg2):  # server side
        """

        :param method:
        :param arg1:
        :param arg2:
        :return:
        """

    def run(self):  # server side
        self.pr_log('listening for conns')
        self.join_chord(self.port)
        while True:
            self.listen_thread()

    ###### end networking rpc methods

    def join_chord(self, port):
        # if first node, seedes this node with all keys
        self.listen_for_key_seed()
        print(repr(self))

        # populate finger init fingertable
        # self.update_finger_table(self.node, 1)
        print(repr(self))


if __name__ == '__main__':
    # invalid usage, print file usage to console
    if len(sys.argv) != 2:
        print('Usage to start new node in new network: ')
        print('python chord_node.py 0')

        print('Usage to join new node to existing network: ')
        print('python chord_node.py [port of existing node]')
        exit(1)

    # store port
    port = int(sys.argv[1])  # todo update to endpoint IP + port

    # create new node
    if port == 0:
        print('>>> Starting new Chord...')
        node = ChordNode(TEST_BASE)
        node.run()
        print('>>> Joined ChordNode {} to new chord'.format(node.node))
        exit(0)

    # join existing chord
    elif port != TEST_BASE:
        print('>>> Trying to join Chord w/ existing node port...')
        node = ChordNode(port)
        node.join_chord(port)
        print('>>> Joined ChordNode {} to existing chord'.format(node.node))
        node.run()
        exit(0)
