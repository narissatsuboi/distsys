"""
Lab 3 Arbitrage Detector (aka forex_subscriber)
:authors: Narissa Tsuboi
:version: 1
:brief:

provider represents publisher in the sub/pub algorithm
Reference:
"""

import socket
import time
from datetime import datetime
import sys
from bellman_ford import BellmanFord
import fxp_bytes_subscriber
import fxp_bytes


class Lab3(object):

    # Global vars per spec
    MSG_BUFFER = 0.1  # 100ms
    STALENESS_TIMEOUT = 1.5  # Threshold for an old quote
    SUBSCRIPTION_TIME = 19  # 10 * 60  # seconds
    USD_TRADE_VAL = 100  # Assume USD is always 100

    def __init__(self, provider):
        """ Instantiates a Lab3 object representing a subscriber. Starts and stores its
        listening socket.

        :param provider: (host, port) of the quote provider
        """

        # represents bellman ford exploration space
        self.graph = {}

        # assumes subscriber always starts on local host
        self.listener_address = (socket.gethostbyname('localhost'), 0)
        listener, time_created = self.start_listener()

        # store provider socket info
        self.provider = (socket.gethostbyname(provider[0]), int(provider[1]))
        self.provider_address, self.provider_port = self.provider[0], self.provider[1]

    def start_listener(self):
        """
        Starts subscriber's listening socket.
        :return listener: listening socket ('address', port)
        :return start_time: datetime object
        """

        # set up listening server
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(self.listener_address)

        # store time created
        start_time = (datetime.utcnow() - datetime.now()) + datetime.now()

        # return listening socket with start time
        return listener, start_time

    def handle_stream(self):
        """

        """

        # accept UDP messages from provider

        pass

    def subscribe(self):
        """
        Pings subscriber with subscription message. New socket created and closed for
        each message. Waits to send next message after 'SUBSCRIPTION_TIME'.
        """

        BUF_SZ = 50
        WAIT = 1.5
        MAX_QUOTES = 50
        QUOTE_SZ = 32  # b

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as subscriber:
            subscribe_msg = fxp_bytes_subscriber.serialize_address(self.listener_address)
            subscriber.sendto(subscribe_msg, self.provider)

        # renew subscription again
        time.sleep(self.SUBSCRIPTION_TIME)

    def run(self):
        """

        """

        # start listener
        self.start_listener()

        # attempt to subscribe
        self.subscribe()


if __name__ == '__main__':
    print('\n/// Forex Subscriber ///')

    # print usage if invalid command line args
    if len(sys.argv) != 3:
        print('Usage: python fxp_bytes_subscriber.py host port')
        exit(1)

    # init subscriber object
    subscriber = Lab3((sys.argv[1], sys.argv[2]))

    # run subscriber object
    subscriber.run()
