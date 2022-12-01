"""


References
(0) header - > https://github.com/nfj5/Distributed-Systems-CPSC5520-FQ19/blob/ddf90183ef6b4da09059af4c137e6004c8f49219/Lab5/lab5.py#L185
(1) version msg -> https://developer.bitcoin.org/reference/p2p_networking.html#version
(2) bitcoin version -> https://developer.bitcoin.org/reference/p2p_networking.html#protocol-versions
(3) byte conversion -> https://docs.python.org/3/library/stdtypes.html#int.from_bytes,
https://docs.python.org/3/library/stdtypes.html#int.to_bytes
(4) python utc to unixtime -> https://stackoverflow.com/questions/16755394/what-is-the-easiest-way-to-get-current-gmt-time-in-unix-timestamp-format
(5) Max BTC buffer size -> https://github.com/nfj5/Distributed-Systems-CPSC5520-FQ19/blob
/ddf90183ef6b4da09059af4c137e6004c8f49219/Lab5/lab5.py#L185
(6) getblocks -> https://developer.bitcoin.org/reference/p2p_networking.html#getblocks
"""

import hashlib
import socket
import sys
import time
from enum import Enum
from socket import error as socket_error
from datetime import datetime
import calendar
from time import strftime, gmtime

BUF_SZ = 2_000_000  # b
BITCOIN_HOST = '95.214.53.160'
BITCOIN_PORT = 8333
BITCOIN_CORE_VERSION = 70015
HDR_SZ = 4 + 12 + 4 + 4  # b
MAGIC = 'f9beb4d9'  # originating network for header


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
        # return pchIPv4 + bytearray((int(x) for x in ipv4_str.split('.')))
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

    def __init__(self, block_num):
        self.block_num = block_num % 10000
        self.host, self.port = '127.0.0.1', 59550
        self.addr = (self.host, self.port)

    def run_cli(self):
        """

        """

        # version
        version_msg = self.make_version_msg()
        version_hdr = self.make_header('version', version_msg)
        version = version_hdr + version_msg

        self.print_msg(version_hdr + version_msg, 'sending')
        response = self.message_node(version)
        self.print_msg(response, 'received')
        # print(response)

        # # verack (hdr only)
        # verack = self.make_header('verack')
        #
        # # block
        # block_msg = self.make_getblocks_msg()
        # block_hdr = self.make_header('getblocks', block_msg)
        # block = block_hdr + block_msg
        #
        # print header msg and version msg


    def message_node(self, b):
        """Sends message to BTC node and waits for response
        :param b: bytes to send as msg
        :returns: response from node
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.settimeout(1500)
            s.connect((BITCOIN_HOST, BITCOIN_PORT))
            s.sendall(b)
            header = s.recv(HDR_SZ)
            print('header', header)
            payload_size = ConvertTo.unmarshal_uint(header[16:20])
            if payload_size > 0:
                payload = s.recv(payload_size)
                print('payload_size', payload_size)
                print('payload', payload)
                return header + payload
            else:
                return header

    @staticmethod
    def get_unix_epoch_time():
        d = datetime.utcnow()
        return calendar.timegm(d.utctimetuple())

    def make_header(self, command, payload=None):
        """ Determines header params and converts to bytes. Returns
        byte str of header information.
        :param command: bitcoin command to send to node
        :param payload: byte str or byte array
        """
        CMD_MAX_LEN = 12  # req'd byte len of encoded command
        MAX_PAYLOAD = 1_000_000 * 32  # ~ 32 MiB, expressed in b

        # magic bytes for originating network, char[4], 4b
        start_string = bytearray.fromhex(MAGIC)  # f9beb4d9 -> bytearray(b'\xf9\xbe\xb4\xd9')
        # command name, char[12], 12b, pad with \0s per spec
        if len(command) < CMD_MAX_LEN:
            command += ('\0' * (CMD_MAX_LEN - len(command)))
        command = command.encode()

        # payload size, uint32_t, 4b
        payload_size = len(payload)
        if payload_size > MAX_PAYLOAD:
            print('Payload size exceeds MAX_SIZE, msg may be dropped or rejected')
        payload_size_b = ConvertTo.uint32_t(payload_size)

        # if no payload
        if payload is None:
            payload = b'0x5df6e0e2'
        # checksum, first 4 bytes of SHA256(SHA256(payload)) char[4], 4b
        checksum = self.checksum(payload)
        header = start_string + command + payload_size_b + checksum
        return header

    def checksum(self, b):
        """ Hashes byte object twice with SHA-256, returns hash
        :param b: byte object to be double hashed
        :returns: hashed(b)
        """
        first_hash = hashlib.sha256(b).digest()
        second_hash = hashlib.sha256(first_hash).digest()
        return second_hash[0:4]

    def make_version_msg(self):
        """
        Creates the version msg that will be sent to the bitcoin node. Recipe for version
        message from reference (1). Reference (3) for byte conversations and
        reference (4) to get unixtime.
        """

        # my protocol, int32_t, 4b
        version = ConvertTo.int32_t(BITCOIN_CORE_VERSION)

        # my services, uint64_t, 8b
        services = ConvertTo.uint64_t(0)

        # my unix epoch time, int64_t, 8b
        timestamp = ConvertTo.int64_t(int(time.time()))

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
        user_agent_bytes = ConvertTo.compactsize_t(0)

        # start_height -> 0, int32_t, 4b
        start_height = ConvertTo.int32_t(0)

        # relay -> False
        relay = ConvertTo.bool_t(False)

        version_msg = version + services + timestamp + addr_recv_services + \
                      addr_recv_ip_addr + addr_recv_port + addr_trans_services + \
                      addr_trans_ip_addr + addr_trans_port + nonce + user_agent_bytes + \
                      start_height + relay

        return version_msg

    def make_getblocks_msg(self):
        """ Used to request an 'inv' msg from BTC node. Reference (6) for data sizes.
        :returns: inv msg in bytes
        """

        # version, uint32_t, 4b
        version = ConvertTo.int32_t(BITCOIN_CORE_VERSION)

        # hashcount, compactSizeuint
        hashcount = ConvertTo.compactsize_t(2)

        # block header hashes, char[32]
        hdr_hashes = bytearray(32)

        # stop hash, char[32], 32
        stop_hash = bytearray(32)

        return version + hashcount + hdr_hashes + stop_hash

    def print_msg(self, msg, text=''):
        print('\n{}MESSAGE'.format('' if text is None else (text + ' ')))
        print('({}) {}'.format(len(msg), msg[:60].hex() + ('' if len(msg) < 60 else
                                                           '...')))
        payload = msg[HDR_SZ:]
        command = self.print_header(msg[:HDR_SZ], self.checksum(payload))
        if command == 'version':
            self.print_version_msg(payload)
        # TODO PRINT VERACK

    @staticmethod
    def print_version_msg(b):
        """Prints formatted list of version_msg, where bytes shown in hex
        :param b: payload from make_version_msg
        """

        # pull out fields
        version, my_services, epoch_time, your_services = b[:4], b[4:12], b[12:20], \
                                                          b[20:28]
        rec_host, rec_port, my_services2, my_host, my_port = b[28:44], b[44:46], \
                                                             b[46:54], b[54:70], \
                                                             b[70:72]
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
        print('{}{:32} version {}'.format(prefix, version.hex(),
                                          ConvertTo.unmarshal_int(version)))
        print('{}{:32} my services'.format(prefix, my_services.hex()))
        time_str = strftime("%a, %d %b %Y %H:%M:%S GMT",
                            gmtime(ConvertTo.unmarshal_int(epoch_time)))
        print('{}{:32} epoch time {}'.format(prefix, epoch_time.hex(), time_str))
        print('{}{:32} your services'.format(prefix, your_services.hex()))
        print(
            '{}{:32} your host {}'.format(prefix, rec_host.hex(),
                                          ConvertTo.ipv6_to_ipv4(rec_host)))
        print('{}{:32} your port {}'.format(prefix, rec_port.hex(),
                                            ConvertTo.unmarshal_uint(rec_port)))
        print('{}{:32} my services (again)'.format(prefix, my_services2.hex()))
        print('{}{:32} my host {}'.format(prefix, my_host.hex(),
                                          ConvertTo.ipv6_to_ipv4(my_host)))
        print('{}{:32} my port {}'.format(prefix, my_port.hex(),
                                          ConvertTo.unmarshal_uint(my_port)))
        print('{}{:32} nonce'.format(prefix, nonce.hex()))
        print('{}{:32} user agent size {}'.format(prefix, user_agent_size.hex(), uasz))
        print('{}{:32} user agent \'{}\''.format(prefix, user_agent.hex(),
                                                 str(user_agent, encoding='utf-8')))
        print('{}{:32} start height {}'.format(prefix, start_height.hex(),
                                               ConvertTo.unmarshal_uint(start_height)))
        print('{}{:32} relay {}'.format(prefix, relay.hex(), bytes(relay) != b'\0'))
        if len(extra) > 0:
            print('{}{:32} EXTRA!!'.format(prefix, extra.hex()))

    def print_header(self, header, expected_cksum=None):
        """
        Report the contents of the given bitcoin message header
        :param header: bitcoin message header (bytes or bytearray)
        :param expected_cksum: the expected checksum for this version message, if known
        :return: command type
        """
        magic, command_hex, payload_size, cksum = header[:4], header[4:16], header[
                                                                            16:20], header[
                                                                                    20:]
        command = str(bytearray([b for b in command_hex if b != 0]), encoding='utf-8')
        psz = ConvertTo.unmarshal_uint(payload_size)
        if expected_cksum is None:
            verified = ''
        elif expected_cksum == cksum:
            verified = '(verified)'
        else:
            verified = '(WRONG!! ' + expected_cksum.hex() + ')'
        prefix = '  '
        print(prefix + 'HEADER')
        print(prefix + '-' * 56)
        prefix *= 2
        print('{}{:32} magic'.format(prefix, magic.hex()))
        print('{}{:32} command: {}'.format(prefix, command_hex.hex(), command))
        print('{}{:32} payload size: {}'.format(prefix, payload_size.hex(), psz))
        print('{}{:32} checksum {}'.format(prefix, cksum.hex(), verified))
        return command


if __name__ == '__main__':
    print('Running client')
    # init client
    my_block = 1697482
    cli = Client(my_block)
    cli.run_cli()
