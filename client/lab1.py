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
NBR_MSG = 'HELLO'  # only msg neighbor clients will accept
BUF_SZ = 1024  # msg buffer size in bs
TIMEOUT = 1.5  # socket timeout duration


class Client:
    def __init__(self, buffer_size=1024, wait=1.5):
        self.buffer_size = buffer_size
        self.wait = wait

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

    @buffer_size.setter
    def buffer_size(self, value) -> int:
        self._buffer_size = value


    @property
    def wait(self) -> int:
        return self._wait

    @wait.setter
    def wait(self, value):
        self._wait = value

    # def get_server_response(self, host, port):
    #     """
    #     Connects to test gcd running at the host and port inputted.
    #     Unpickles msg rec'd. On valid msg sends pickled response of other
    #     hosts and ports to the connected socket.
    #
    #     :param host: IP/hostname
    #     :param port: port number of GCD
    #     :return:  message
    #     """
    #
    #     # create socket
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         # connect socket
    #         s.settimeout(TIMEOUT)
    #         try:
    #             s.connect((HOST, GCD_PORT))
    #         except socket_error as serr:
    #             print('failed to connect to server: %s' % serr)
    #             sys.exit(1)
    #         s.sendall(pickle.dumps(GCD_MSG))
    #
    #         # receive data
    #         try:
    #             data = s.recv(BUF_SZ)
    #         except socket_error as serr:
    #             print('error receiving data: %s' % serr)
    #             sys.exit(1)
    #
    #         # handle server response
    #         try:
    #             gcd_response = pickle.loads(data)
    #         except(pickle.PickleError, KeyError, EOFError):
    #             gcd_response = 'error: ' + str(data)
    #         else:
    #             if 'Unexpected message' in gcd_response:
    #                 gcd_response = 'error: unexpected message'
    #
    #         return gcd_response
    #
    # def get_neighbor_response(self, host, port):
    #     """
    #     Given host and port, returns msg rec'd from host. Handles
    #     connection, no response, invalid format, and invalid msg with
    #     error msgs to console.
    #
    #     :param host: IP/hostname
    #     :param port: port number
    #     :return:  message
    #     """
    #
    #     # create socket
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         # connect socket
    #         s.settimeout(TIMEOUT)
    #         try:
    #             s.connect((host, port))
    #         except socket_error as serr:
    #             print('failed to connect: {} %s' % serr)
    #             return
    #         s.sendall(pickle.dumps(NBR_MSG))
    #
    #         # receive data
    #         try:
    #             data = s.recv(BUF_SZ)
    #         except socket.timeout(TIMEOUT) as terr:
    #             print('no response: {} %s' % terr)
    #             return
    #
    #         # handle neighbor response
    #         try:
    #             response = pickle.loads(data)
    #         except(pickle.PickleError, KeyError, EOFError):
    #             response = 'error: ' + str(data)
    #         else:
    #             if 'Unexpected message' in response:
    #                 response = 'ERROR: Neighbor only accepts HELLO as msg'
    #
    #         return response

    def send_message(self, host, port, msg):
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
            s.settimeout(self.wait)
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

    # handle invalid command line args
    # if len(sys.argv) != 3:
    #     print("Usage: python3 lab1.py HOST PORT")
    #     exit(1);

    # HOST, GCD_PORT = sys.argv[1], int(sys.argv[2])  # 23600
    HOST, GCD_PORT = 'localhost', int('23600')  # 23600

    # init client
    client = Client()

    # connect to group coordinator daemon
    gcd_response = client.send_message(HOST, GCD_PORT, GCD_MSG)
    if not gcd_response:
        print(gcd_response)
        sys.exit(1)

    print(GCD_MSG + ' (' + str(HOST) + ', ' + str(GCD_PORT) + ')')

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
