"""
Lab 3 Arbitrage Detector (aka forex_subscriber)
:authors: Narissa Tsuboi
:version: 1
:brief:

provider represents publisher in the sub/pub algorithm
References

https://docs.python.org/3/library/threading.html for threaded processes
"""

import socket
import time
from datetime import datetime
import sys
from bellman_ford import BellmanFord
import fxp_bytes_subscriber
import fxp_bytes

# Global vars per spec
BUF_SZ = 4096
MSG_BUFFER = 0.1  # 100ms
SUBSCRIPTION_TIME = 19  # 10 * 60  # seconds
USD_TRADE_VAL = 100  # Assume USD is always 100
RUNTIME = 15 #10 * 60  # Run for 10 minutes per spec
TIMESTAMP, CROSS, PRICE = 'timestamp', 'cross', 'price'


class Lab3(object):


    def __init__(self, provider):
        """ Instantiates a Lab3 object representing a subscriber. Starts and stores its
        listening socket.

        :param provider: (host, port) of the quote provider
        """

        # represents bellman ford exploration space
        self.graph = {}

        # subscriber always starts on local host at hardkeyed port number
        self.listener_address = (socket.gethostbyname('localhost'), 45678)

        # store provider socket info
        self.provider = (socket.gethostbyname(provider[0]), int(provider[1]))
        self.provider_address, self.provider_port = self.provider[0], self.provider[1]

    def subscribe(self):
        """
        Pings subscriber with subscription message. New socket created and closed for
        each message. Waits to send next message after 'SUBSCRIPTION_TIME'.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as subscriber:
            subscribe_msg = fxp_bytes_subscriber.serialize_address(self.listener_address)
            subscriber.sendto(subscribe_msg, self.provider)
            print('subscribe: sent subscribe message to pub')

    def handle_stream(self):
        """

        """

        markets_ts  = {}  # holds markets processed

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
            listener.bind((self.listener_address))
            print('\nblocking, waiting to receive message from forex ')

            # time each prev msg was rec'd, seed with time of listener creation
            previous_time = (datetime.utcnow() - datetime.now()) + datetime.now()

            while True:
                b_provider_msg, _addr = listener.recvfrom(BUF_SZ)
                quote_list = fxp_bytes_subscriber.unmarshall_msg(b_provider_msg)

                # handle each quote in the quote list (list of dicts, ea dict is a quote)
                for quote in quote_list:
                    print(quote)
                    print(quote[TIMESTAMP])


    def is_out_of_order(quote):
        """Quotes may come out of order since this is UDP/IP, so the process
        should ignore any quotes with timestamps before the latest one seen
        for that market.

        {CURR1/CURR2 : ts , ... }
        """

        pass




    def remove_stale_rates(self):
        """
        Remove exchage rates that have been in the graph for longer than the staleness
        limit

        :return: number of rates that were removed for being stale
        """

        STALENESS_TIMEOUT = 1.5  # Threshold for an old quote
        pass

    def run(self):
        """

        """

        # attempt to subscribe
        self.subscribe()

        # end loop after RUNTIME per spec
        end = time.time() + RUNTIME
        while time.time() < end:
            self.handle_stream()

        print('END OF PROGRAM')
        return

    def print_quote(self, quote):
        """
        Prints a quote in the following format:
        'YEAR-MO-DAY HR:MI:SE CROSS1 CROSS2 RATE'

        eg input:
        """
        ts = quote[TIMESTAMP]
        cross = quote[CROSS]
        price = quote[PRICE]
        print(ts, cross, price)

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

    # TODO REMOVE
    sys.exit(0)

