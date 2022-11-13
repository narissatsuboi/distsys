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


POSSIBLE_HOSTS = ['127.0.01']
POSSIBLE_PORTS = [43543, 43544, 43545, 43546]




class ChordNode(object):
    global M, NODES
    # node ip lookup, see lookup_node(n)
    node_map = None

    def __init__(self, n):
        # easy access node info
        self.port = n
        self.addr = ('127.0.0.1', n)
        self.node_id = self.hash_node(*self.addr)
        self.pr_log('__init__ populated lookup table')

        # init finger table, idx starts at 1
        self.finger = [None] + [FingerEntry(self.node_id, k) for k in range(1, M+1)]
        self.pr_log('__init__ finger table')
        self.predecessor = None
        self.keys = {}

        # threading start TODO DONT THINK THIS CALL IS NEEDED
        # listening_thread = threading.Thread(target=self.listen_thread(), args=(self.addr))
        # listening_thread.start()
        #

        # log
        self.pr_log('__init__ complete')

    def pr_log(self, msg):
        """Logs node activities"""
        log = '>>> {} : id {} | {} | {}'.format(self.addr, self.node_id, msg,
                                                datetime.now().timestamp().conjugate())
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

    @staticmethod
    def lookup_node(n):
        # generate precomputed map {node_ids : addr ...}
        if ChordNode.node_map is None:
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
            ChordNode.node_map = nm
        # fetch addr off other node
        # lookup in precomputed table
        return ChordNode.node_map[n]

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


    def join_chord(self):
        pass

    ###### end chord algo methods

    ###### start networking rpc methods

    def query_handler(self): # TODO chord_query
        """ a querier to talk to any arbitrary node in the network to query a value for a
        given key or add a key/value pair (with replacement)"""

    def listen_for_key_seed(self):
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
        self.listen_for_key_seed()
        while True:
            self.listen_thread()


    ###### end networking rpc methods


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Usage to start new node in new network: ')
        print('python chord_node.py 0')

        print('Usage to join new node to existing network: ')
        print('python chord_node.py [port of existing node]')

    # port = int(sys.argv[1])  # todo update to endpoint IP + port
    port = 43543
    # create new node
    node = ChordNode(port)
    node.run()

    # TODO join existing chord
    # if port != 0:
    #     node.join_chord(port)
    #     print('Joined ChordNode {} to existing chord')
