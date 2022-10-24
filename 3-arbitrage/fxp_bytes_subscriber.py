"""
Forex Subscriber
:authors: Narissa Tsuboi
:version: 1
:brief: Subscriber utility class for Forex Subscriber (Lab3.py). Utility functions
mirror the serialize and deserialize utility functions for the corresponding provider
class forex_provider_v2.py.

References:
Python Arrays for byte manip https://docs.python.org/3/library/array.html

"""

import fxp_bytes as fxp

from ipaddress import ip_address
import socket
import sys
from array import array

"""
Format of the subscription request message is 4-byte IPv4 address in big-endian 
(network format) followed by a 2-byte port number also in big-endian. 
"""


def deserialize_price(b: bytes) -> float:
    """
    Convert a byte array representing a price to float.

    :param b: 8-byte array of floating point numbers
    :return: float representation of b
    """

    price = array('d')  # init new array, of type 'd' float
    price.frombytes(b)  # fill with decoded float val eg array([9006104071832581.0])
    return price[0]


def serialize_address(address: tuple) -> bytes:
    """
    Converts (str, int) tuple to 6 byte array. Format of the subscription request message
    is 4-byte IPv4 address in big-endian (network format) followed by a 2-byte port number
    also in big-endian.

    :param address: str, int tuple representing and ip and port
    :return: 6-bytes representing ip and port
    """

    byte_ip = socket.inet_aton(address[0])
    byte_port = socket.inet_aton(str(address[1]))[2:]

    return byte_ip + byte_port


if __name__ == '__main__':
    print('')
