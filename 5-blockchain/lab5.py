"""


References
(1) version msg -> https://developer.bitcoin.org/reference/p2p_networking.html#version
(2) bitcoin version -> https://developer.bitcoin.org/reference/p2p_networking.html#protocol-versions
(3) byte conversion -> https://docs.python.org/3/library/stdtypes.html#int.from_bytes,
https://docs.python.org/3/library/stdtypes.html#int.to_bytes
(4) python utc to unixtime -> https://stackoverflow.com/questions/16755394/what-is-the-easiest-way-to-get-current-gmt-time-in-unix-timestamp-format

"""

import pickle
import socket
from socket import error as socket_error
from datetime import datetime, date
import calendar

BUF_SZ = 4096
BITCOIN_HOST = '97.126.42.129'
BITCOIN_PORT = 8333
BITCOIN_CORE_VERSION = 70015


class ConvertTo(object):
    @staticmethod
    def compactsize_t(n):
        if n < 252:
            return ConvertTo.uint8_t(n)
        if n < 0xffff:
            return ConvertTo.uint8_t(0xfd) + ConvertTo.uint16_t(n)
        if n < 0xffffffff:
            return ConvertTo.uint8_t(0xfe) + ConvertTo.uint32_t(n)
        return ConvertTo.uint8_t(0xff) + ConvertTo.uint64_t(n)

    @staticmethod
    def unmarshal_compactsize(b):
        key = b[0]
        if key == 0xff:
            return b[0:9], ConvertTo.unmarshal_uint(b[1:9])
        if key == 0xfe:
            return b[0:5], ConvertTo.unmarshal_uint(b[1:5])
        if key == 0xfd:
            return b[0:3], ConvertTo.unmarshal_uint(b[1:3])
        return b[0:1], ConvertTo.unmarshal_uint(b[0:1])

    @staticmethod
    def bool_t(flag):
        return ConvertTo.uint8_t(1 if flag else 0)

    @staticmethod
    def ipv6_from_ipv4(ipv4_str):
        pchIPv4 = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff])
        return pchIPv4 + bytearray((int(x) for x in ipv4_str.split('.')))

    @staticmethod
    def ipv6_to_ipv4(ipv6):
        return '.'.join([str(b) for b in ipv6[12:]])

    @staticmethod
    def uint8_t(n):
        return int(n).to_bytes(1, byteorder='little', signed=False)

    @staticmethod
    def uint16_t(n):
        return int(n).to_bytes(2, byteorder='little', signed=False)

    @staticmethod
    def int32_t(n):
        return int(n).to_bytes(4, byteorder='little', signed=True)

    @staticmethod
    def uint32_t(n):
        return int(n).to_bytes(4, byteorder='little', signed=False)

    @staticmethod
    def int64_t(n):
        return int(n).to_bytes(8, byteorder='little', signed=True)

    @staticmethod
    def uint64_t(n):
        return int(n).to_bytes(8, byteorder='little', signed=False)

    @staticmethod
    def unmarshal_int(b):
        return int.from_bytes(b, byteorder='little', signed=True)

    @staticmethod
    def unmarshal_uint(b):
        return int.from_bytes(b, byteorder='little', signed=False)


class Client(object):

    def __init__(self):
        self.host, self.port = '127.0. 0.1', 55555
        self.addr = (self.host, self.port)

    @staticmethod
    def get_unix_epoch_time():
        d = datetime.utcnow()
        return calendar.timegm(d.utctimetuple())

    def make_version_msg(self):
        """
        Creates the version msg that will be sent to the bitcoin node to init TCP
        handshake. Recipe for version message from reference (1) in the header of this
        file. Reference (3) for byte conversations and reference (4) to get unixtime.
        """

        #TODO: IP AND PORT MAY NEED TO BE SWITCHED TO BIG END

        # my protocol, int32_t, 4b
        version = ConvertTo.int32_t(BITCOIN_CORE_VERSION)

        # my services, uint64_t, 8b
        services = ConvertTo.uint64_t(0)

        # my unix epoch time, int64_t, 8b
        timestamp = ConvertTo.int64_t(self.get_unix_epoch_time())

        # host's services (assume 0x01), uint64_t, 8b
        addr_recv_services = ConvertTo.uint64_t(1)

        # host's addr IPv6 or IPv4 mapped IPv6 16b, char[16], big end
        addr_recv_ip_addr = ConvertTo.ipv6_from_ipv4(BITCOIN_HOST)

        # host's port, uint16_t,big end, 2b
        addr_recv_port = ConvertTo.uint16_t(BITCOIN_PORT)

        # addr_trans servs, same as services above, uint64_t, 8b
        addr_trans_services = services

        # my IPv6 or IPv4 mapped IPv6, char[16], big end, 16b
        addr_trans_ip_addr = ConvertTo.ipv6_from_ipv4(self.host)

        # my port, uint16_t, big end, 2b
        addr_trans_port = ConvertTo.uint16_t(self.port)

        # nonce, uint64_t, 8b
        nonce = ConvertTo.uint64_t(0)

        # compactSizeuint, user_agent_bytes -> 0, 4b
        compactSizeuint = ConvertTo.compactsize_t(0)

        # start_height -> 0, int32_t, 4b
        start_height = ConvertTo.int32_t(0)

        # relay -> False
        relay = ConvertTo.bool_t(False)

        version_msg = version + services + timestamp + addr_recv_services + \
                      addr_recv_ip_addr + addr_recv_port + addr_trans_services + \
                      addr_trans_ip_addr + addr_trans_port + nonce + compactSizeuint + \
                      start_height + relay
        return version_msg


if __name__ == '__main__':
    print('data')
    cli = Client()
    print(cli.make_version_msg())
