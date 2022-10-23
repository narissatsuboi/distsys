"""
Forex Subscriber
:authors: Narissa Tsuboi
:version: 1
:brief: Subscriber side class for Forex Provider, a 3rd party vendor that publishes
currency exchange rates via UDP IP socket in the form of a byte array.
Reference: test publisher  forex_provider_v2.py
"""
import ipaddress
import socket
import sys
from array import array

"""
Format of the subscription request message is 4-byte IPv4 address in big-endian 
(network format) followed by a 2-byte port number also in big-endian. 
"""


class ForexSubscriber(object):
    """
    Subscribes to ForexProvider object.
    """
    BUF_SZ = 12
    WAIT = 1.5

    def __init__(self, host, port):
        """
        Instantiates a ForexSubscriber object used to subscribe to a ForexPublisher.
        :param host: ForexSubscriber host address
        :param port: ForexSubscriber port number
        """

        # rename local host to its ip representation
        if host == 'localhost':
            host = '127.0.0.1'
        self.host, self.port = host, int(port)
        self.listener, self.listener_address = self.start_a_server()

    @staticmethod
    def start_a_server():
        """
        Opens a listening socket to handle publish msgs rec'd from
        ForexPublisher.

        :return: listener socket and address
        """
        # set up listening server
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(('localhost', 0))  # use any free socket
        print('start_a_server: udp listening socket up and running...')
        return listener, listener.getsockname()

    def subscribe(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as subscriber:
            byte_ip = socket.inet_aton(self.host)
            byte_port = socket.inet_aton(str(self.port))[2:]
            subscribe_msg = byte_ip + byte_port
            address = (self.host, self.port)
            subscriber.sendto(subscribe_msg, address)
        print('subscribe: sent msg')
    def run_forever(self):
        self.subscribe()
        while True:
            continue


if __name__ == '__main__':
    print('\n/// Forex Subscriber ///')

    # print usage if invalid command line args
    if len(sys.argv) != 3:
        print('Usage: python fxp_bytes_subscriber.py host port')
        exit(1)

    # attempt to connect to publisher
    HOST, PORT = sys.argv[1], sys.argv[2]
    subscriber = ForexSubscriber(HOST, PORT)  # init subscriber
    print('Attempting to connect to Forex Publisher...')
    print('Host: {} Port: {}'.format(HOST, PORT))
    subscriber.run_forever()

