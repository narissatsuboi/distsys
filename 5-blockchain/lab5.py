"""


References
(1) version msg -> https://developer.bitcoin.org/reference/p2p_networking.html#version
(2) bitcoin version -> https://developer.bitcoin.org/reference/p2p_networking.html#protocol-versions
(3) byte conversion -> https://docs.python.org/3/library/stdtypes.html#int.from_bytes,
https://docs.python.org/3/library/stdtypes.html#int.to_bytes
(4) python utc to unixtime -> https://stackoverflow.com/questions/16755394/what-is-the-easiest-way-to-get-current-gmt-time-in-unix-timestamp-format

"""

import hashlib
import socket
from socket import error as socket_error
from datetime import datetime, date
import calendar
from time import strftime, gmtime

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
        self.host, self.port = '127.0. 0.1', 59550
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

    def print_version_msg(self, b):
        """Prints formatted list of version_msg, where bytes shown in hex
        :param b: payload from make_version_msg
        """

        # pull out fields
        version, my_services, epoch_time, your_services = b[:4], b[4:12], b[12:20], b[
                                                                                    20:28]
        rec_host, rec_port, my_services2, my_host, my_port = b[28:44], b[44:46], b[
                                                                                 46:54], b[
                                                                                         54:70], b[
                                                                                                 70:72]
        nonce = b[72:80]
        user_agent_size, uasz = ConvertTo.unmarshal_compactsize(b[80:])
        i = 80 + len(user_agent_size)
        user_agent = b[i:i + uasz]
        i += uasz
        start_height, relay = b[i:i + 4], b[i + 4:i + 5]
        extra = b[i + 5:]

        # print report
        prefix = '  '
        print(prefix + 'VERSION')
        print(prefix + '-' * 56)
        prefix *= 2
        print('{}{:32} version {}'.format(prefix, version.hex(), ConvertTo.unmarshal_int(version)))
        print('{}{:32} my services'.format(prefix, my_services.hex()))
        time_str = strftime("%a, %d %b %Y %H:%M:%S GMT",
                            gmtime(ConvertTo.unmarshal_int(epoch_time)))
        print('{}{:32} epoch time {}'.format(prefix, epoch_time.hex(), time_str))
        print('{}{:32} your services'.format(prefix, your_services.hex()))
        print(
            '{}{:32} your host {}'.format(prefix, rec_host.hex(), ConvertTo.ipv6_to_ipv4(rec_host)))
        print('{}{:32} your port {}'.format(prefix, rec_port.hex(),
                                            ConvertTo.unmarshal_uint(rec_port)))
        print('{}{:32} my services (again)'.format(prefix, my_services2.hex()))
        print('{}{:32} my host {}'.format(prefix, my_host.hex(), ConvertTo.ipv6_to_ipv4(my_host)))
        print('{}{:32} my port {}'.format(prefix, my_port.hex(), ConvertTo.unmarshal_uint(my_port)))
        print('{}{:32} nonce'.format(prefix, nonce.hex()))
        print('{}{:32} user agent size {}'.format(prefix, user_agent_size.hex(), uasz))
        print('{}{:32} user agent \'{}\''.format(prefix, user_agent.hex(),
                                                 str(user_agent, encoding='utf-8')))
        print('{}{:32} start height {}'.format(prefix, start_height.hex(),
                                               ConvertTo.unmarshal_uint(start_height)))
        print('{}{:32} relay {}'.format(prefix, relay.hex(), bytes(relay) != b'\0'))
        if len(extra) > 0:
            print('{}{:32} EXTRA!!'.format(prefix, extra.hex()))


if __name__ == '__main__':
    print('data')
    cli = Client()
    version_msg = cli.make_version_msg()
    cli.print_version_msg(version_msg)

