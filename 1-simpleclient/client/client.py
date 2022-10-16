""""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1

:brief: A simple client that connects to a Group Coordinator Daemon (
GCD) which responds with a pickled list of potential group members.
Sends a message to each group member, prints their response,
then exits.
"""
import pickle
import socket
from socket import error as socket_error
import sys


class Client(object):
    """
    Client object attempts to perform process in file brief.
    """

    BUF_SZ = 1024  # msg buffer size in bs

    def __init__(self, host, port):
        """
        Instantiates a client object to connect with GCD and neighbor nodes.

        :param host: host name
        :param port: port number of host
        """

        self.host, self.port = host, port
        self.members = []
        self.timeout = 1.5  # seconds

    def send_message(self, host, port, msg) -> str:
        """
        Given host and port, returns msg rec'd from host. Handles
        connection, no response, invalid format, and invalid msg with
        error msgs to console.

        :param host: IP/hostname
        :param port: port number
        :return:  message
        """

        # create socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # connect socket
            s.settimeout(self.timeout)
            try:
                s.connect((host, port))
            except socket_error as serr:
                print('failed to connect: {} %s' % serr)
                return
            s.sendall(pickle.dumps(msg))

            # receive data
            try:
                pick_data = s.recv(self.buffer_size)
            except socket_error as serr:
                print('failed to return response: {} %s' % serr)
                return

            # handle neighbor response
            try:
                unpick_data = pickle.loads(pick_data)
            except(pickle.PickleError, KeyError, EOFError):
                unpick_data = 'error: ' + str(unpick_data)

        return unpick_data


if __name__ == '__main__':

    GCD_MSG = 'JOIN'  # only msg GCD will accept
    NBR_MSG = 'HELLO'  # only msg neighbor clients will accept


    # handle invalid command line args
    if len(sys.argv) != 3:
        print("Usage: python client.py HOST PORT")
        exit(1);

    HOST, GCD_PORT = sys.argv[1], int(sys.argv[2])

    # init client
    client = Client(BUF_SZ, TIMEOUT)

    # get valid gcd response or exit
    print(GCD_MSG + ' (' + str(HOST) + ', ' + str(GCD_PORT) + ')')
    gcd_response = client.send_message(HOST, GCD_PORT, GCD_MSG)
    if type(gcd_response) is not list:
        print(gcd_response)
        sys.exit(1)

    # print responses from neighbor nodes
    for pair in gcd_response:
        host, port = pair['host'], pair['port']
        print('HELLO to ' + repr(pair))
        neighbor_response = client.send_message(host, port, NBR_MSG)

        # skip to next neighbor if no response
        if neighbor_response is None:
            continue
        print(neighbor_response)

    sys.exit(0)