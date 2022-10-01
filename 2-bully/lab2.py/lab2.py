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
        #self.selector = selectors.DefaultSelector()
        #self.listener, self.listener_address = self.start_a_server()




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Bully')
    # handle invalid command line args count
    if len(sys.argv) != 3:
        print("Usage: python3 lab2.py (IP, port) 'YYYY-MM-DD' suid")
        exit(1)


