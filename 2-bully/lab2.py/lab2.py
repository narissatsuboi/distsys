""""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1
:brief:

References
https://docs.python.org/3/library/selectors.html

"""
import selectors   # used to wait for I/O readiness notification on multiple file objects
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
        self.pid = (days_to_birthday, int(su_id))
        self.members = {}
        self.states = {}
        self.bully = {}  # None means election is pending, otherwise pid of bully
        self.selector = selectors.DefaultSelector()
        self.listener, self.listener_address = self.start_a_server()

    @staticmethod
    def start_a_server():
        # set up listening server
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(('localhost', 0))
        listener.listen()
        return listener, listener.getsockname()

        # TODO where does this go? its not static so it can't go in start_a_server
        # # set up the selectors (bag of sockets)
        # selector = selectors.DefaultSelector()
        # selector.register(server, selectors.EVENT_READ)
        #
        # # selector loop
        # while True:
        #     events = self.selector.select(CHECK_INTERVAL)
        pass

    def join_group(self):
        pass

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

        # create socket thru handle response

    @classmethod
    def send(cls, peer, message_name, message_date=None, wait_for_reply=False,
             buffer_size=BUF_SZ):
        pass


    def run(self):
        pass

    def accept_peer(self):
        pass

    def receive_message(self, peer):
        pass

    def check_timeouts(self):
        pass

    def get_connection(self, member):
        pass

    def is_election_in_progress(self):
        pass

    def is_expired(self, peer=None, threshold=ASSUME_FAILURE_TIMEOUT):
        pass

    def set_leader(self, new_leader):
        pass

    def get_state(self, peer=None, switch_mode=False):
        """
        Look up current state in state table.

        :param peer: socket connected to peer process (None means self)
        :param switch_mode: if True, then state and timestamp are both returned
        :return: either the state or (state, timestamp) depending on the detail (not
        found gives(QUIESCENT, None))
        """

        if peer is None:
            peer = self
        status = self.states[peer] if peer in self.states else (State.QUIESCENT, None)
        return status if switch_mode else status[0]

    def set_state(self, state, peer=None, switch_mode=False):
        pass

    def set_quiescent(self, peer=None):
        pass

    def start_election(self, reason):
        pass

    def declare_victory(self, reason):
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
    if len(sys.argv) != 3:
        print("Usage: python3 lab2.py (IP, port) 'YYYY-MM-DD' suid")
        exit(1)


