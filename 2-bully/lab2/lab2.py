""""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1
:brief:

References
https://docs.python.org/3/library/selectors.html

"""
import selectors  # used to wait for I/O readiness notification on multiple file objects
import socket
from enum import Enum
from socket import error as socket_error
import pickle
import sys
import datetime
from datetime import datetime
from datetime import timedelta

# TODO confirm or justify this value
CHECK_INTERVAL = 1.5  # ms to wait before checking for events in list serv

# TODO figure out what this is and what the actual number is supposed to be
PEER_DIGITS = 1

# TODO justify
ASSUME_FAILURE_TIMEOUT = 5

BUF_SZ = 1024


class State(Enum):
    """
    Enumeration of state a peer can have for the Lab2 class.
    """
    QUIESCENT = 'QUIESCENT'  # erase any memory of this peer

    # outgoing msg is pending
    SEND_ELECTION = 'ELECTION'
    SEND_VICTORY = 'COORDINATOR'
    SEND_OK = 'OK'

    # incoming msg is pending

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
    Group Coordinator Daemon (GCD)
    """

    # TODO Figure out the format that next_birthday is assumed to be
    def __init__(self, gcd_address, next_birthday, su_id):
        """
        Constructs a Lab2 object to talk to the given GCD

        :param gcd_address:  IP address (sysarg[0]), port (sysarg[1])
        :param next_birthday: users next birthday in iso-str format 'YEAR-MO-DY'
        :param su_id: user's six digit seattle u id
        """

        self.gcd_address = (gcd_address[0], int(gcd_address[1]))
        days_to_birthday = (datetime.fromisoformat(
            next_birthday) - datetime.now()).days
        self.pid = (int(days_to_birthday), int(su_id))
        self.members = {}  # {pid: (host, port), ...}
        self.states = {}  #  { socket:pid, ...}
        self.bully = {}  # None means election is pending, otherwise pid of bully
        self.selector = selectors.DefaultSelector()
        self.listener, self.listener_address = self.start_a_server()
        self.set_state(State.WAITING_FOR_ANY_MESSAGE)

    @staticmethod
    def start_a_server():
        # set up listening server
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(('localhost', 0))  # use any free socket
        listener.listen(100)  # allow backlog of 100
        listener.setblocking(False)  # non blocking socket
        return listener, listener.getsockname()  # getsockname format (host, port)

    def join_group(self):
        """
        Retrieves member list from GCD, deserializes, and assigns to member list field.
        """
        # opens connection to gcd, sends JOIN msg, recvs msg, and closes connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gcd:
            JOIN = ('JOIN', (self.pid, self.listener_address))
            gcd.connect(self.gcd_address)
            gcd.sendall(pickle.dumps(JOIN))
            self.members = pickle.loads(gcd.recv(BUF_SZ))

    def start_election(self, reason):
        """ Send ELECTION message to all peers that are bigger than me"""
        print('in start_election')
        # set state
        self.set_state(State.SEND_ELECTION)

        is_leader = True

        # check if I'm the leader
        for member_pid in self.members:
            print(member_pid)

            # skip myself
            if member_pid == self.pid:
                continue

        # logic to only send election msgs to peers with pids greater than mine
        for member_pid in self.members:
            if member_pid == self.pid:  # skip myself
                continue

            # for peers greater than me
            if member_pid[0] > self.pid[0] or \
                    (member_pid[0] == self.pid[0] and member_pid[1] > self.pid[1]):
                new_socket = self.get_connection(member_pid)
                self.send_message(new_socket)  # send 'ELECTION'

    def send_message(self, peer):
        """
        Send the queued msg to the given peer (based on its current state

        :param peer:
        :return:
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

    def send(self, peer, message_name, message_data=None, wait_for_reply=False,
             buffer_size=BUF_SZ):

        if self.is_election_in_progress():
            message_name = self.get_state(self)
            self.set_state(State.WAITING_FOR_OK)

        peer.sendall(pickle.dumps((message_name, message_data)))

        # register
        self.selector.register(peer, selectors.EVENT_READ)

    def run(self):
        """
        Runs event loop
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

    def receive_message(self, peer):
        pass

    @staticmethod
    def receive(peer, buffer_siz=BUF_SZ):
        pass

    def check_timeouts(self):
        pass

    def get_connection(self, member_pid):
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.connect(self.members[member_pid])
        new_socket.setblocking(False)
        return new_socket
        # TODO handle if member can't be connected to

    def is_election_in_progress(self):
        """
        Checks my state to see if we are awaiting a victor.
        """
        if self.states[self.pid] == State.WAITING_FOR_VICTOR:
            return True
        return False

    def is_expired(self, peer=None, threshold=ASSUME_FAILURE_TIMEOUT):
        pass

    def set_leader(self, new_leader):
        """
        Empty bully dict and store newest bully by {pid : new_leader}
        """
        self.bully.clear()
        self.bully[new_leader.pid] = new_leader

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
        # update my state
        # send message to everyone else
        pass

    def update_members(self, their_idea_of_membership):
        pass

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
    #my_peer.start_election(State.SEND_ELECTION)
    print('>>> RUNNING EVENT LOOP')
    my_peer.run()
