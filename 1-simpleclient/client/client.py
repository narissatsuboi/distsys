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

    def join_group(self):
        """
        Attempts to connect to GCD. If connect successful, sends JOIN message to GCD
        and expects to receive dictionary of members and addresses. Then calls
        meet_members. If connect unsuccessful or GCD response of wrong type, logs to
        console.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gcd:
            gcd_address = (self.host, self.port)
            print('JOIN {}'.format(gcd_address))
            gcd.settimeout(self.timeout)
            try:
                gcd.connect(gcd_address)
            except socket_error as err:
                print('failed to connect to gcd: {} &s' % err)
                return

    @staticmethod
    def send_message(sock, data, buffer_size=BUF_SZ):
        """
        Marshalls data and sends to given socket. Blocks waiting for response,
        unmarshalls and returns response. If send fails, logs and returns

        :param sock: socket to send message and recv message on
        :param data: data to send via message
        :param buffer_size: num bytes in recv buffer
        :return: message
        """

        # send pickled data on sock
        try:
            sock.sendall(pickle.dumps(data))
        except socket_error as err:
            print('failed to send msg to socket: {} &s' % err)
            return

        # recv response, unpickle, and return
        return pickle.loads(sock.recv(buffer_size))

if __name__ == '__main__':

    GCD_MSG = 'JOIN'  # only msg GCD will accept
    NBR_MSG = 'HELLO'  # only msg neighbor clients will accept


    # handle invalid command line args
    if len(sys.argv) != 3:
        print("Usage: python client.py HOST PORT")
        exit(1)

    # store parameters needed to init Client object, then init
    HOST, GCD_PORT = sys.argv[1], int(sys.argv[2])
    client = Client(HOST, GCD_PORT)

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