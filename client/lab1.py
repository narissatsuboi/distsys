""""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1

:brief: A simple client that connects to a Group Coordinator Daemon (
GCD) which responds with a pickeled list of potential group members.
Sends a message to each group member, prints their response,
then exits.
"""
import pickle
import socket
from socket import error as socket_error
import sys

GCD_MSG = 'JOIN'  # only msg GCD will accept
NBR_MSG = 'HELLO' # only msg neighbor clients will accept
BUF_SZ = 1024     # msg buffer size in bs
TIMEOUT = 1.5     # socket timeout duration


def get_server_response(host, port):
    """
    Connects to test gcd running at the host and port inputted.
    Unpickles msg rec'd. On valid msg sends pickled response of other
    hosts and ports to the connected socket.

    :param host: IP/hostname
    :param port: port number of GCD
    :return:  message
    """

    # create socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # connect socket
        s.settimeout(TIMEOUT)
        try:
            s.connect((HOST, GCD_PORT))
        except socket_error as serr:
            print('failed to connect to server: %s' % serr)
            sys.exit(1)
        s.sendall(pickle.dumps(GCD_MSG))

        # receive data
        try:
            data = s.recv(BUF_SZ)
        except socket_error as serr:
            print('error receiving data: %s' % serr)
            sys.exit(1)

        # handle server response
        try:
            gcd_response = pickle.loads(data)
        except(pickle.PickleError, KeyError, EOFError):
            gcd_response = 'error: ' + str(data)
        else:
            if 'Unexpected message' in gcd_response:
                gcd_response = 'error: unexpected message'

        return gcd_response


def get_neighbor_response(host, port):
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
        s.settimeout(TIMEOUT)
        try:
            s.connect((host, port))
        except socket_error as serr:
            print('failed to connect: {} %s' % serr)
            return
        s.sendall(pickle.dumps(NBR_MSG))

        # receive data
        try:
            data = s.recv(BUF_SZ)
        except socket.timeout(TIMEOUT) as terr:
            print('no response: {} %s' % terr)
            return

        # handle neighbor response
        try:
            response = pickle.loads(data)
        except(pickle.PickleError, KeyError, EOFError):
            response = 'error: ' + str(data)
        else:
            if 'Unexpected message' in response:
                response = 'ERROR: Neighbor only accepts HELLO as msg'

        return response


if __name__ == '__main__':

    # handle invalid command line args
    if len(sys.argv) != 3:
        print("Usage: python3 lab1.py HOST PORT")
        exit(1);

    HOST = sys.argv[1]
    GCD_PORT = int(sys.argv[2])  # 23600

    # connect to group coordinator daemon
    gcd_response = get_server_response(HOST, GCD_PORT)
    print(GCD_MSG + ' (' + str(HOST) + ', ' + str(GCD_PORT) + ')')

    # handle string response (error)
    if type(gcd_response) is not list:
        print(gcd_response)
        sys.exit(1)

    # print responses from neighbor nodes
    for pair in gcd_response:
        host, port = pair['host'], pair['port']
        print('HELLO to ' + repr(pair))
        neighbor_response = get_neighbor_response(host, port)

        # skip to next neighbor if no response
        if neighbor_response is None:
            continue
        print(neighbor_response)

    sys.exit(0)