"""
:file: fxp_bytes_subsriber.py
:authors: Narissa Tsuboi
:version: 1
:brief: Subscriber utility for Forex Subscriber (Lab3.py). Utility functions
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
import datetime
from datetime import datetime


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

    :param address: (str, int) tuple representing and ip and port
    :return: 6-bytes representing ip and port
    """

    byte_ip = socket.inet_aton(address[0])
    byte_port = socket.inet_aton(str(address[1]))[2:]

    return byte_ip + byte_port


def deserialize_cross(b: bytes) -> str:
    """
    Converts 8-bit ASCII characers to strings.

    :param b:byte array
    :return: fromated string eg 'GBP/USD'
    """
    s = b.decode()
    return s[0:3] + '/' + s[3:]


def deserialize_datetime(b: bytes) -> datetime:
    """
    Convert an 8 byte big-endian byte array to a microseconds. Switches from big to
    little endian. Datetime object in byte array represents a UTC timestamp for a
    corresponding provider message.

    :param b: byte array
    :return: datetime in microsecs
    """

    MICROS_PER_SEC = 1e+6

    dt = array('L')  # store bits in long array
    dt.frombytes(b)  # fill array
    dt.byteswap()  # big to little endian

    print('dt[0', dt[0])
    # calculate the UTC time
    timestamp_in_micro = dt[0] / MICROS_PER_SEC  # convert from sec to microsec

    # timestamp_in_micro = dt[0] / 1e+6  # convert from sec to microsec
    print('timestamp in micro', timestamp_in_micro)
    # calculate the microsecs from timestamp to now

    # TODO convert to timedelta calc instead
    return datetime.fromtimestamp(timestamp_in_micro) + (datetime.utcnow() -
                                                         datetime.now())


def unmarshall_msg(b: bytes) -> list:
    """
    Unmarshall a byte msg into a formated list of dicts representing Forex quotes.

    :param b: 32b array msg from Forex provider in the following format
    <timestamp, currency 1, currency 2, exchange rate>
    b[0:8]   - timestamp, 64b int num of microseconds in UTC, big endian
    b[8:14]  - currency names as ISO codes 'USD, 'GDP' in 8b ASCII from left to right
    b[14:22] - exchange rate as a 64b float in little endian
    b[22:32] - reserved, not used, set to x00

    :returns: a list of dicts representing Forex quotes

    """
    TIMESTAMP, CROSS, PRICE = 'timestamp', 'cross', 'price'

    MSG_SZ = 32      # per spec, each quote is no more than 32 bytes
    quote_list = []  # holds unmarshalled list of dictionaries representing quotes

    # calculate the total number of quotes contained in the UDP byte array
    tot_msg_size = len(b)
    n_quotes = int(tot_msg_size / MSG_SZ)

    # populate quotes into list of dicts
    for i in range(n_quotes):
        quote = {}

        # get the bytes the next quote in the list
        start_quote = i * MSG_SZ
        end_quote = start_quote + MSG_SZ
        b_quote = b[start_quote:end_quote]

        b_time, b_cross, b_price = b_quote[0:8], b_quote[8:14], b_quote[14:22]

        quote[TIMESTAMP] = deserialize_datetime(b_time)
        quote[CROSS] = deserialize_cross(b_cross)
        quote[PRICE] = deserialize_price(b_price)

        quote_list.append(quote)

    return quote_list


if __name__ == '__main__':
    print()
