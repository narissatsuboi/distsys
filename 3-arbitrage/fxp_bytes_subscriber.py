"""
Forex Subscriber
:authors: Narissa Tsuboi
:version: 1
:brief: Subscriber side class for Forex Provider, a 3rd party vendor that publishes
currency exchange rates via UDP IP socket in the form of a byte array.
Reference: test publisher  forex_provider_v2.py
"""
import sys

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
        self.host, self.port = host, port


# Press the green button in the gutter to run the script.
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