""""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1
:brief: An implementation of the 'Bully' algorithm used to dynamically achieve
consensus by choosing a leader from a group of distributed processes. The intent
of the implementation is to execute asynchronously using nonblocking sockets and
state machine.

THIS LAB IS UNFINISHED AND DOES NOT RUN, I COULD NOT FIGURE IT OUT
AFTER 25 HRS.

References
https://docs.python.org/3/library/selectors.html
https://en.wikipedia.org/wiki/Bully_algorithm
"""

import selectors  # used to wait for I/O readiness notification on multiple file objects
import socket
from enum import Enum
from socket import error as socket_error
import pickle
import sys
import datetime
from datetime import datetime

BUF_SZ = 1024  # max msg size in bytes
CHECK_INTERVAL = 1.5  # ms to wait before checking for events in list serv
PEER_DIGITS = 10  # used to shorten the port numbers is cpr_sock
ASSUME_FAILURE_TIMEOUT = 5  # ms to wait before assuming host has failed
QUEUE_SIZE = 100


class State(Enum):
    """
    Enumeration of state a peer can have for the Lab2 class.
    """
    QUIESCENT = 'QUIESCENT'  # erase any memory of this peer

    # outgoing msg is pending
    SEND_ELECTION = 'ELECTION'
    SEND_VICTORY = 'COORDINATOR'
    SEND_OK = 'OK'

    # when I've sent an ELECTION msg
    WAITING_FOR_OK = 'WAIT_OK'

    # only applies to myself
    WAITING_FOR_VICTOR = 'WHO IS THE WINNER?'

    # when I've done an accept on their connect to my server
    WAITING_FOR_ANY_MESSAGE = 'WAITING'

    def is_incoming(self):
        """ Categorization helper. """
        return self not in (State.SEND_ELECTION, State.SEND_VICTORY, State.SEND_OK)


class Lab2(object):
    """
    Implementation of a single node that has its own identity (pid), can join the
    network of other nodes by connecting with the Group Coordinator Daemon (GCD),
    and participate in elections.
    """

    def __init__(self, gcd_address, next_birthday, su_id):
        """
        Constructs a Lab2 object to talk to the given GCD

        :param gcd_address:  IP address (sysarg[0]), port (sysarg[1])
        :param next_birthday: users next birthday in iso-str format 'YEAR-MO-DY'
        :param su_id: user's six digit seattle u id
        """

        # address and port of gcd
        self.gcd_address = (gcd_address[0], int(gcd_address[1]))

        # calculates the unique parameter for this node's pid
        days_to_birthday = (datetime.fromisoformat(
            next_birthday) - datetime.now()).days

        # unique node process id
        self.pid = (int(days_to_birthday), int(su_id))

        # dictionary of all members known to this node
        self.members = {}  # {pid: (host, port), ...}

        # dictionary of the states of all members known to this node
        self.states = {}  # { socket:pid, ...}

        # identity of the current leader
        self.bully = None  # None means election is pending, otherwise pid of bully

        # tcp socket selector
        self.selector = selectors.DefaultSelector()

        # server side listener socket
        self.listener, self.listener_address = self.start_a_server()

    def run(self):
        """
        Runs event loop and performs action on sockets queued up in selector.
        """

        # register MY listening socket
        self.selector.register(self.listener, selectors.EVENT_READ)

        # selector loop
        while True:
            events = self.selector.select(CHECK_INTERVAL)

            print(events)

            for key, mask in events:
                if key.fileobj == self.listener:  # accept peer
                    self.accept_peer()
                elif mask and selectors.EVENT_READ:  # recv msg
                    self.receive_message(key.fileobj)
                else:  # mask and selectors.EVENT_WRITE
                    self.send_message(key.fileobj)  # send msg
            self.check_timeouts()

    def accept_peer(self):
        """
        Accept new TCP/IP connections from a peer (TCP handshake)
        """
        print('in accept_peer')
        try:
            peer, _addr = self.listener.accept()
            print('{}: accepted [{}]'.format(self.pr_sock(peer), self.pr_now()))
            self.set_state(State.WAITING_FOR_ANY_MESSAGE, peer)
        except socket_error as serr:
            print('accept failed {}'.format(serr))

    def join_group(self):
        """
        Joins the other live notes via the Group Coordinator Daemon.
        Retrieves member list from GCD, deserializes, and assigns to member list field.
        """

        # opens connection to gcd, sends JOIN msg, recvs msg, and closes connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gcd:
            # GCD accepts tuple of pid and listener socket address only
            data = (self.pid, self.listener_address)
            print('JOIN {}, {}'.format(self.gcd_address, data))  # log

            # attempt to connect to the gcd
            gcd.connect(self.gcd_address)

            # get members dict by using send method
            self.members = self.send(gcd, 'JOIN', data, wait_for_reply=True)

            # expect a dictionary from the GCD, if not raise error
            if type(self.members) != dict:
                raise TypeError('wrong data type from GCD: {}'.format(self.members))

    def start_election(self, reason):
        """
        Send ELECTION message to all peers that outrank this node.

        :param reason: note for log
        """
        print('Starting an election {}'.format(reason))

        self.set_state(State.SEND_ELECTION)  # set MY state, election now in progress

        am_leader = True  # flag for biggest bully not found

        # logic to only send election msgs to peers with pids greater than mine
        for member in self.members:
            if member > self.pid:
                peer = self.get_connection(member)
                if peer is None:
                    continue
                self.set_state(State.SEND_ELECTION, peer)
                am_leader = False  # found someone bigger than me
        if am_leader:
            self.declare_victory('no other members bigger than me')

    def send_message(self, peer):
        """
        Send the queued msg to the given peer.
        :param peer: socket connected to the socket selector in run
        """

        state = self.get_state(peer)
        print('{}: sending {} [{}]'.format(self.pr_sock(peer), state.value,
                                           self.pr_now()))
        try:
            # should be ready, but may be a failed connect instead
            self.send(peer, state.value, self.members)

        except ConnectionError as err:  # TODO better exception handling later
            print('error sending exiting send_msg')
            pass
        except Exception as err:
            print('error sending exiting send_msg')
            pass

        # check to see if we want to wait for response immediately
        if state == State.SEND_ELECTION:
            self.set_state(State.WAITING_FOR_OK, peer, switch_mode=True)
        else:
            self.set_quiescent(peer)

    def send(cls, peer, message_name, message_data=None, wait_for_reply=False,
             buffer_size=BUF_SZ):
        """
        Marshalls and sends the msg to the given socket and unmarshalls the returned
        msg.

        :param peer: socket to send and recv from
        :param message_name: text message name 'OK', 'ELECTION'
        :param message_data: data to be marshalled
        :param wait_for_reply: only True if blocking desired
        :param buffer_size: if blocking, buffer size
        :return: if blocking, returns response else None
        """

        # assemble and send msg to peer
        message = message_name if message_data is None else (message_name, message_data)
        peer.sendall(pickle.dumps(message))

        # if blocking, wait for a reply
        if wait_for_reply:
            return cls.receive(peer, buffer_size)

    def receive_message(self, peer):
        """
        Recv msg from peer and update state based on ELECTION, COORDINATOR, OK.

        :param peer: socket to recv from
        """

        # recv msg from peer, handle connection error and socket errors
        try:
            message_name, their_idea = self.receive(peer)
            print('{}: received {} [{}]'.format(self.pr_sock(peer), message_name, self.pr_now()))
        except ConnectionError as err:
            print('closing: {}'.format(err))
            self.set_quiescent(peer)
            return
        except socket_error as serr:
            print('failed {}'.format(serr))
            if self.is_expired(peer):
                print('peer timed out')
                self.set_quiescent(peer)
            return

        # update members with their idea of state
        self.update_members(their_idea)

        # make state transition based on rec'd msg
        if message_name == 'ELECTION':
            self.set_state(State.SEND_OK, peer)
            if not self.is_election_in_progress():
                self.start_election('Got a VOTE card')
        elif message_name == 'COORDINATOR':
            self.set_leader('someone else is the leader')
            self.set_quiescent(peer)
            self.set_quiescent()
        elif message_name == 'OK':
            if self.get_state() == State.WAITING_FOR_OK:
                self.set_state(State.WAITING_FOR_VICTOR)  #recd an OK ignore others
            self.set_quiescent(peer)

    @staticmethod
    def receive(peer, buffer_size=BUF_SZ):
        """
        Recvs and unmarshalls incoming msg from the peer.

        :param peer: socket to recv msg from
        :param buffer_size: buffer size of the listening socket
        :return: unmarshalled msg
        """

        # store buffer
        packet = peer.recv(buffer_size)

        # handle None response when socket is closed
        if not packet:
            raise ValueError('socket closed')

        # unmarshall data and return
        data = pickle.loads(packet)
        if type(data) == str:
            data = (data, None)  # format msg into tuple
        return data

    def check_timeouts(self):
        """
        Check if peers (including me) have timed out.
        """

        if self.is_expired():
            if self.get_state() == State.WAITING_FOR_OK:
                self.declare_victory('timed out from waiting from ok from peers')
            else:
                self.start_election('timed out waiting for coordinate from peers')

    def get_connection(self, member):
        """
        Get a socket for a member. Connection will be non-blocking,
        must use selector to pick it up when its writable.

        :param member_pid: process id of peer
        :return: socket
        """

        # look up member's address
        listener = self.members[member]
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.setblocking(False)

        try:
            peer.connect(listener)
        except BlockingIOError:  # handle connection still in progress
            pass
        except socket_error as serr:
            print('FAILURE: couldnt connect to member {}'.format(serr))
            return None

        return peer

    def is_election_in_progress(self):
        """
        Checks my state to see if we are awaiting a victor.
        """
        return self.bully is None

    def is_expired(self, peer=None, threshold=ASSUME_FAILURE_TIMEOUT):
        """
        Check if peers state was set more than threshold seconds ago. If so,
        peer expired.

        :param peer: socket connected to peer process, None means self
        :param threshold: seconds to wait since last state change
        :return: True if past threshold
        """
        my_state, when = self.get_state(peer, detail=True)
        if my_state == State.QUIESCENT:
            return False
        time_since = (datetime.now() - when).total_seconds()
        return time_since > threshold

    def set_leader(self, new_leader):
        """
        Set the current leader. Sets self.bully to that leader.  
        """
        self.bully = new_leader
        print('Leader is {}'.format(self.pr_leader()))

    def get_state(self, peer=None, switch_mode=False):
        """
        Look up member's current state in state table.

        :param peer: socket connected to peer process (None means self)
        :param switch_mode: if True, then state and timestamp are both returned
        :return: either the state or (state, timestamp) depending on the detail (not
        found gives(QUIESCENT, None))
        """

        if not switch_mode:
            peer = self
        status = self.states[peer] if peer in self.states else (State.QUIESCENT, None)
        return status if switch_mode else status[0]

    def set_state(self, state, peer=None, switch_mode=False):
        """
        Set a member's state in the state table.

        :param peer: socket connected to peer process (None means self)
        :param switch_mode: if True, then state and timestamp are both returned
        """

        if not switch_mode:
            peer = self
        self.states[peer] = state

    def set_quiescent(self, peer=None):
        """ call when you've sent an election out and didn't hear back in time from
        this peer, then update their state """

        if not peer:
            peer = self
        self.set_state(State.QUIESCENT, peer)

    def declare_victory(self, reason):
        """ Send COORDINATOR message to all peers stating I am the bully"""

        # call set_leader
        self.set_leader(self.pid)
        # update my state
        self.set_state(State.SEND_VICTORY)
        # send message to everyone else
        for member_pid in self.members:
            if member_pid == self.pid:  # skip myself
                continue
            new_socket = self.get_connection(member_pid)
            self.send_message(new_socket)

    def update_members(self, their_idea_of_membership):
        pass

    @staticmethod
    def start_a_server():
        """
        Opens a non-blocking listening socket on localhost.

        :return: listener socket and address
        """
        # set up listening server
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(('localhost', 0))  # use any free socket
        listener.listen(QUEUE_SIZE)
        listener.setblocking(False)  # non blocking socket
        return listener, listener.getsockname()

    @staticmethod
    def pr_now():
        """ Printing helper for current timestamp """
        return datetime.now().strftime('%H:%M:%S.%f')

    def pr_sock(self, sock):
        """ Printing helper for given socket """
        if sock is None or sock == self or sock == self.listener:
            return 'self'
        return self.cpr_sock(sock)

    @staticmethod
    def cpr_sock(sock):
        """ Static version of helper for printing given socket """
        l_port = sock.getsockname()[1] % PEER_DIGITS

        try:
            r_port = sock.getpeername()[1] % PEER_DIGITS
        except OSError:
            r_port = '???'
        return '{}->{} ({})'.format(l_port, r_port, id(sock))

    def pr_leader(self):
        """ Printing helper for current leader's name """
        return 'unknown' if self.bully is None else ('self' if self.bully == self.pid
                                                     else self.bully)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Bully')
    # handle invalid command line args count
    if len(sys.argv) != 5:
        print("Usage: python3 lab2 (IP, port) 'YYYY-MM-DD' suid")
        exit(1)

    HOST, GCD_PORT, NEXT_BDAY, SUID = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    my_peer = Lab2((HOST, GCD_PORT), NEXT_BDAY, SUID)
    print('>>> NEW PEER CREATED')
    my_peer.join_group()
    print('>>> JOINED GROUP')
    print('>>> MEMBERSLIST')
    print(my_peer.members)
    print('>>> STARTING ELECTION')
    my_peer.start_election(State.SEND_ELECTION)
    print('>>> RUNNING EVENT LOOP')
    my_peer.run()
