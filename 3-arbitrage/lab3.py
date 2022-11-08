"""
Lab 3 Arbitrage Detector (aka forex_subscriber)
:authors: Narissa Tsuboi
:version: 1
:brief:

provider represents publisher in the sub/pub algorithm
References

"""
import math
import socket
import sys
import time
from datetime import datetime, timedelta

import fxp_bytes_subscriber
from bellman_ford import BellmanFord

# Global vars per spec
BUF_SZ = 4096           # bytes
SUBSCRIPTION_TIME = 19  # 10 * 60  # seconds
TIME_TO_STALE = 1.5     # Threshold for an old quote
USD_TRADE_VAL = 100     # Assume USD is always 100
RUNTIME = 10 * 60       # Run for 10 minutes per spec

# commonly used dict keys
TIMESTAMP, CROSS, PRICE = 'timestamp', 'cross', 'price'


def print_quote(quote):
    """
    Prints a quote in the following format:
    'YEAR-MO-DAY HR:MI:SE CROSS1 CROSS2 RATE'

    eg input:
    """
    ts = quote[TIMESTAMP]
    cross = ' '.join(quote[CROSS].split('/'))
    price = quote[PRICE]
    print(ts, cross, price)


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

        self.markets_ts = {}  # holds markets processed

    def subscribe(self):
        """
        Pings subscriber with subscription message. New socket created and closed for
        each message. Waits to send next message after 'SUBSCRIPTION_TIME'.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sub:
            subscribe_msg = fxp_bytes_subscriber.serialize_address(self.listener_address)
            sub.sendto(subscribe_msg, self.provider)
            print('subscribe: sent subscribe message to pub')

    def handle_stream(self):
        """
        Opens listening socket. Processes UDP packets rec'd by unmarshalling them and
        directing them to the Bellman Ford object.
        """

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
            listener.bind(self.listener_address)
            print('\nblocking, waiting to receive message from forex ')

            while True:
                b_provider_msg, _addr = listener.recvfrom(BUF_SZ)
                quote_list = fxp_bytes_subscriber.unmarshall_msg(b_provider_msg)

                for quote in quote_list:
                    # check if it's out of order, if not, add to graph, else skip
                    if not self.is_out_of_order(quote[CROSS], quote[TIMESTAMP]):
                        print_quote(quote)  # log

                        # convert price to -log and add quote to graph
                        quote[PRICE] = (-1) * math.log(quote[PRICE])
                        self.add_quote_to_graph(quote)
                    else:
                        print('ignoring out-of-sequence message')
                # remove stale quotes from the graph then call bellman ford
                self.remove_stale_rates()
                self.run_bellman_ford()

    def add_quote_to_graph(self, quote):
        """
        Processes a quote's rate and adds it to self.graph. Constructs directional and
        bidirectional edges as appropriate.

        :param quote: dictionary representing a forex quote
        """

        curr_a, curr_b = quote[CROSS].split('/')

        """add directional edge between start and end vertices. start vertex not in 
        graph, create entry in graph with nested dict as value 
        holding end vertex as key and timestamp and rate as value"""
        if curr_a not in self.graph:
            self.graph[curr_a] = {}

        # add edge (a->b) rate from start to end vertex
        self.graph[curr_a][curr_b] = {TIMESTAMP: quote[TIMESTAMP], PRICE: quote[PRICE]}

        # add edge (b->a) rate from end vertex to start, if applicable
        if curr_b not in self.graph:
            self.graph[curr_b] = {}
        self.graph[curr_b][curr_a] = {TIMESTAMP: quote[TIMESTAMP], PRICE: (-1) * quote[
            PRICE]}

    def run_bellman_ford(self, tolerance=1e-10):
        """
        Runs the Bellman Ford algorithm and prints the results to console.
        :param tolerance:
        :return: (dist, prev, neg_edge) tuple
        """

        # init bf object with graph
        mybf = BellmanFord(self.graph)
        dist, prev, neg_edge = mybf.shortest_paths('USD')

        # if a negative edge was found, print the arbitrage report
        if neg_edge:
            self.print_arbitrage(prev, 'USD')

    def print_arbitrage(self, prev, src):
        """
        Prints the path to log messages
        :param prev: locations where currency was previously recorded
        :param src: starting currency
        """

        path, end = [src], prev[src]

        while not end == src:
            path.append(end)
            end = prev[end]

        path.append(src)
        path.reverse()
        value = 100
        last = src
        print('ARBITRAGE:')
        print('\tstart with 100 {}'.format(src))

        for _ in range(1, len(path)):
            curr = path[_]
            value *= math.exp(-1 * self.graph[last][curr]["price"])
            print("\t\texchange {} for {} {}".format(last, curr, value))
            last = curr

        print("\t\tarbitrage gains {} {}".format(value - 100, src))

    def is_out_of_order(self, cross, ts):
        """Quotes may come out of order since this is UDP/IP, so the process
        should ignore any quotes with timestamps before the latest one seen
        for that market.
        """
        if cross not in self.markets_ts or \
                (cross in self.markets_ts and ts > self.markets_ts[cross]):
            self.markets_ts[cross] = ts
            return False

        return True

    def remove_stale_rates(self):
        """
        Remove exchage rates that have been in the graph for longer than
        STALENESS_TIMEOUT

        :return: tuple of whoses quote was removed
        """
        stale_time = datetime.utcnow() - timedelta(seconds=TIME_TO_STALE)

        to_delete = []

        for currency_a in self.graph:
            for currency_b in self.graph[currency_a]:
                if self.graph[currency_a][currency_b][TIMESTAMP] <= stale_time:
                    to_delete.append((currency_a, currency_b))
        for item in to_delete:
            print('removing stale quote for ({}, {})'.format([item[0]], [item[1]]))
            del self.graph[item[0]][item[1]]

    def run(self):
        """Subscribes and runs for RUNTIME."""

        # attempt to subscribe
        self.subscribe()

        # end loop after RUNTIME per spec
        end = time.time() + RUNTIME
        while time.time() < end:
            self.handle_stream()

        print('END OF PROGRAM')
        return


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

    sys.exit(0)
