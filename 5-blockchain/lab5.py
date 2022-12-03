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
(7) compactuint -> https://btcinformation.org/en/developer-reference#compactsize
-unsigned-integers
(8) block header -> https://btcinformation.org/en/developer-reference#compactsize-unsigned-integers
block zero -> https://en.bitcoin.it/wiki/Genesis_block
swap endian -> https://www.folkstalk.com/2022/10/python-little-endian-to-big-endian-with
-code-examples.html
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

# networking globals
CLI_HOST, CLI_PORT = '127.0.0.1', 59550  # requestor addr
BTC_HOST, BTC_PORT = '95.214.53.160', 8333  # sync node addr
CLI_ADDR, BTC_ADDR = (CLI_HOST, CLI_PORT), (BTC_HOST, BTC_PORT)
MAX_BUF_SZ = 2_000_000  # b

# btc protocol globals
MSG_HDR_SZ = 24  # b
BTC_CORE_VERSION = 70015
MAINNET = 'f9beb4d9'
TIME = int(time.time())

# block 0 globals
BTC_HASH_BLOCK_ZERO = bytes.fromhex(
    '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
BTC_HASH_MERKLE_ROOT = bytes.fromhex(
    '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b')


class Conversion(object):
    """ Helper class for byte and unit conversions. All int conversions are little
    endian. """

    @staticmethod
    def swap_endianness(b):
        """
        Swaps the endianness of a byte array, little to big or big to little.
        :param b: bytes or bytearray
        :return: bytearray of swapped endianness
        """
        b = bytearray.fromhex(b.hex())
        b.reverse()
        return b

    @staticmethod
    def compactsize_t(n):
        """
        Converts an integer into a compact uint.
        :param n: integer
        :return: compactuint
        """
        if n < 252:
            return Conversion.uint8_t(n)
        if n < 0xffff:
            return Conversion.uint8_t(0xfd) + Conversion.uint16_t(n)
        if n < 0xffffffff:
            return Conversion.uint8_t(0xfe) + Conversion.uint32_t(n)
        return Conversion.uint8_t(0xff) + Conversion.uint64_t(n)

    @staticmethod
    def unmarshal_compactsize(b):
        """
        Converts a compact uint to an uint.
        :param b: bytes or bytearray
        :return: uint
        """
        key = b[0]
        if key == 0xff:
            return b[0:9], Conversion.unmarshal_uint(b[1:9])
        if key == 0xfe:
            return b[0:5], Conversion.unmarshal_uint(b[1:5])
        if key == 0xfd:
            return b[0:3], Conversion.unmarshal_uint(b[1:3])
        return b[0:1], Conversion.unmarshal_uint(b[0:1])

    @staticmethod
    def bool_t(flag):
        """
        Converts bool to 8 bit uint.
        :param flag: bool
        :return: uint8
        """
        return Conversion.uint8_t(1 if flag else 0)

    @staticmethod
    def ipv6_from_ipv4(ipv4_str):
        """
        Maps an ipv4 address expressed as a string to ipv6 format.
        :param ipv4_str: string expression of ipv4 address
        :return: string expression of ipv6 address
        """
        pchIPv4 = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff])
        # return pchIPv4 + bytearray((int(x) for x in ipv4_str.split('.')))
        return pchIPv4 + bytearray((int(x) for x in ipv4_str.split('.')))

    @staticmethod
    def ipv6_to_ipv4(ipv6):
        """
        Maps an ipv6 address expressed as a string to ipv4 format.
        :param ipv6_str: string expression of ipv6 address
        :return: string expression of ipv4 address
        """
        return '.'.join([str(b) for b in ipv6[12:]])

    @staticmethod
    def uint8_t(n):
        """
        Converts a value to 8-bit unsigned byte string.
        :param n: int
        :return: uint8
        """
        return int(n).to_bytes(1, byteorder='little', signed=False)

    @staticmethod
    def uint16_t(n):
        """
        Converts a value to 16-bit unsigned byte string.
        :param n: int
        :return: uint16
        """
        return int(n).to_bytes(2, byteorder='little', signed=False)

    @staticmethod
    def int32_t(n):
        """
        Converts a value to 32-bit signed byte string.
        :param n: int
        :return: int32
        """
        return int(n).to_bytes(4, byteorder='little', signed=True)

    @staticmethod
    def uint32_t(n):
        """
        Converts a value to 32-bit unsigned byte string.
        :param n: int
        :return: uint32
        """
        return int(n).to_bytes(4, byteorder='little', signed=False)

    @staticmethod
    def int64_t(n):
        """
        Converts a value to 64-bit signed byte string.
        :param n: int
        :return: int64
        """
        return int(n).to_bytes(8, byteorder='little', signed=True)

    @staticmethod
    def uint64_t(n):
        """
        Converts a value to 64-bit unsigned byte string.
        :param n: int
        :return: uint64
        """
        return int(n).to_bytes(8, byteorder='little', signed=False)

    @staticmethod
    def unmarshal_int(b):
        """
        Converts bytes to signed integer.
        :param b: bytes
        :return: int
        """
        return int.from_bytes(b, byteorder='little', signed=True)

    @staticmethod
    def unmarshal_uint(b):
        """
        Converts bytes to unsigned integer.
        :param b: bytes
        :return: int
        """
        return int.from_bytes(b, byteorder='little', signed=False)


class Cli(object):

    @staticmethod
    def make_msg_header(command, payload=None):
        """ Determines header params and converts to bytes. Returns
        byte str of header information.
        :param command: bitcoin command to send to node
        :param payload: byte str or byte array
        """
        CMD_MAX_LEN = 12  # req'd byte len of encoded command

        # magic bytes for originating network, char[4], 4b
        start_string = bytearray.fromhex(
            MAINNET)  # f9beb4d9 -> bytearray(b'\xf9\xbe\xb4\xd9')
        # command name, char[12], 12b, pad with \0s per spec
        if len(command) < CMD_MAX_LEN:
            command += ('\0' * (CMD_MAX_LEN - len(command)))
        command = command.encode()

        # if no payload
        if payload is None:
            payload = ''.encode()
        payload_size_bytes = Conversion.uint32_t(len(payload))
        checksum = Cli.checksum(payload)
        header = start_string + command + payload_size_bytes + checksum
        return header

    @staticmethod
    def checksum(b):
        """ Hashes byte object twice with SHA-256, returns last 4 digits
        :param b: byte object to be double hashed
        :returns: hashed(b)[0:4]
        """
        first_hash = hashlib.sha256(b).digest()
        second_hash = hashlib.sha256(first_hash).digest()
        return second_hash[0:4]

    @staticmethod
    def double_sha256(b):
        """ Hashes byte object twice with SHA-256, returns hash
        :param b: byte object to be double hashed
        :returns: hashed(b)
        """
        first_hash = hashlib.sha256(b).digest()
        second_hash = hashlib.sha256(first_hash).digest()
        return second_hash

    @staticmethod
    def make_version_msg():
        """
        Creates the version msg that will be sent to the bitcoin node. Recipe for version
        message from reference (1). Reference (3) for byte conversations and
        reference (4) to get unixtime.
        """

        # my protocol, int32_t, 4b
        version = Conversion.int32_t(BTC_CORE_VERSION)

        # my services, uint64_t, 8b
        services = Conversion.uint64_t(0)

        # my unix epoch time, int64_t, 8b
        timestamp = Conversion.int64_t(int(time.time()))

        # host's services (assume 0x01), uint64_t, 8b
        addr_recv_services = Conversion.uint64_t(1)

        # host's addr IPv6 or IPv4 mapped IPv6 16b, char[16], big end
        addr_recv_ip_addr = Conversion.ipv6_from_ipv4(BTC_HOST)

        # host's port, uint16_t,big end, 2b
        addr_recv_port = Conversion.uint16_t(BTC_PORT)

        # addr_trans servs, same as services above, uint64_t, 8b
        addr_trans_services = services

        # my IPv6 or IPv4 mapped IPv6, char[16], big end, 16b
        addr_trans_ip_addr = Conversion.ipv6_from_ipv4(CLI_HOST)

        # my port, uint16_t, big end, 2b
        addr_trans_port = Conversion.uint16_t(CLI_PORT)

        # nonce, uint64_t, 8b
        nonce = Conversion.uint64_t(0)

        # compactSizeuint, user_agent_bytes -> 0, 4b
        user_agent_bytes = Conversion.compactsize_t(0)

        # start_height -> 0, int32_t, 4b
        start_height = Conversion.int32_t(0)

        # relay -> False
        relay = Conversion.bool_t(False)

        version_msg = version + services + timestamp + addr_recv_services + \
                      addr_recv_ip_addr + addr_recv_port + addr_trans_services + \
                      addr_trans_ip_addr + addr_trans_port + nonce + user_agent_bytes + \
                      start_height + relay

        return version_msg

    @staticmethod
    def make_block_header():
        """ Returns block header

        """
        # block version, int32_t, 4b
        block_version = Conversion.int32_t(4)
        # prev block header, char[32], 32b
        # prev_block_header_hash = self.double_sha256(''.encode())
        # print('sys size', sys.getsizeof(prev_block_header_hash))
        # prev_block_header_hash = self.double_sha256(bytearray(32))
        prev_block_header_hash = BTC_HASH_BLOCK_ZERO

        # merkle root hash, char[32], 32b
        merkle_root_hash = prev_block_header_hash
        # time, uint32_t, 4b
        time = Conversion.uint32_t(TIME)
        # nBits, uint32_t, 4b
        nbits = Conversion.uint32_t(0)
        # nonce, uint32_t, 4b
        nonce = Conversion.uint32_t(0)

        # print('block version', block_version)
        print('prev block header hash', prev_block_header_hash)
        # print('merkle_root_hash', merkle_root_hash)
        # print('time', time)
        # print('nbits', nbits, nbits.hex())
        # print('nonce', nonce, nonce.hex())
        block_header_hash = block_version + prev_block_header_hash + merkle_root_hash + time + nbits \
                            + nonce
        print('blockheaderhash', block_header_hash, sys.getsizeof(block_header_hash))
        return block_header_hash

    @staticmethod
    def make_getblocks_msg():
        """ Used to request an 'inv' msg from BTC node. Reference (6) for data sizes.
        :returns: inv msg in bytes
        """

        version = Conversion.uint32_t(BTC_CORE_VERSION)
        hashcount = Conversion.compactsize_t(1)
        hdr_hashes = Conversion.swap_endianness(BTC_HASH_BLOCK_ZERO)
        print('hdr_hashes', hdr_hashes)
        stop_hash = bytearray(32)

        return version + hashcount + hdr_hashes + stop_hash

    @staticmethod
    def print_msg(msg, text=''):
        print('\n{}MESSAGE'.format('' if text is None else (text + ' ')))
        print('({}) {}'.format(len(msg), msg[:60].hex() + ('' if len(msg) < 60 else
                                                           '...')))
        payload = msg[MSG_HDR_SZ:]
        command = Cli.print_header(msg[:MSG_HDR_SZ], Cli.checksum(payload))
        if command == 'version':
            Cli.print_version_msg(payload)
        elif command == 'getblocks':
            Cli.print_getblocks(payload)

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
        user_agent_size, uasz = Conversion.unmarshal_compactsize(b[80:])
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
                                          Conversion.unmarshal_int(version)))
        print('{}{:32} my services'.format(prefix, my_services.hex()))
        time_str = strftime("%a, %d %b %Y %H:%M:%S GMT",
                            gmtime(Conversion.unmarshal_int(epoch_time)))
        print('{}{:32} epoch time {}'.format(prefix, epoch_time.hex(), time_str))
        print('{}{:32} your services'.format(prefix, your_services.hex()))
        print(
            '{}{:32} your host {}'.format(prefix, rec_host.hex(),
                                          Conversion.ipv6_to_ipv4(rec_host)))
        print('{}{:32} your port {}'.format(prefix, rec_port.hex(),
                                            Conversion.unmarshal_uint(rec_port)))
        print('{}{:32} my services (again)'.format(prefix, my_services2.hex()))
        print('{}{:32} my host {}'.format(prefix, my_host.hex(),
                                          Conversion.ipv6_to_ipv4(my_host)))
        print('{}{:32} my port {}'.format(prefix, my_port.hex(),
                                          Conversion.unmarshal_uint(my_port)))
        print('{}{:32} nonce'.format(prefix, nonce.hex()))
        print('{}{:32} user agent size {}'.format(prefix, user_agent_size.hex(), uasz))
        print('{}{:32} user agent \'{}\''.format(prefix, user_agent.hex(),
                                                 str(user_agent, encoding='utf-8')))
        print('{}{:32} start height {}'.format(prefix, start_height.hex(),
                                               Conversion.unmarshal_uint(start_height)))
        print('{}{:32} relay {}'.format(prefix, relay.hex(), bytes(relay) != b'\0'))
        if len(extra) > 0:
            print('{}{:32} EXTRA!!'.format(prefix, extra.hex()))

    @staticmethod
    def print_header(header, expected_cksum=None):
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
        psz = Conversion.unmarshal_uint(payload_size)
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

    @staticmethod
    def print_getblocks(b):
        """
        :param b: get_blocks msg in bytes
        """

        version, count, header_hash, stop_hash = b[:4], b[4:5], b[5:37], b[37:]
        # version, count, header_hash, stop_hash = b[:4], b[4:8], b[8:40], b[40:]

        padding = '  '
        print('count', count.hex())
        print(padding + 'GETBLOCKS')
        print(padding + '-' * 56)
        padding *= 2
        print(
            '{}{:32} version {}'.format(padding, version.hex(), Conversion.unmarshal_int(
                version)))
        print('{}{:32} hashcount {}'.format(padding, count.hex(),
                                            Conversion.unmarshal_compactsize(count)[1]))
        print('{}{:32} header hash'.format(padding, header_hash.hex()[:32]))
        print('{}{:32} stop hash'.format(padding, stop_hash.hex()[:32]))


if __name__ == '__main__':
    print('Running client')
    # init client
    my_block = 1697482 % 10000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BTC_HOST, BTC_PORT))

    # version
    version_msg = Cli.make_version_msg()
    version_hdr = Cli.make_msg_header('version', version_msg)
    version = version_hdr + version_msg
    Cli.print_msg(version_hdr + version_msg, 'sending')
    s.sendall(version)
    header = s.recv(MSG_HDR_SZ)
    payload_size = Conversion.unmarshal_uint(header[16:20])
    payload = s.recv(payload_size)
    # response = self.message_node(version)
    Cli.print_msg(header + payload, 'received')

    # verack (hdr only)
    verack = Cli.make_msg_header('verack')
    Cli.print_msg(verack, 'sending')
    s.sendall(verack)
    header = s.recv(MSG_HDR_SZ)
    # response = self.message_node(verack)
    Cli.print_msg(header, 'received')

    # # block
    block_msg = Cli.make_getblocks_msg()
    block_hdr = Cli.make_msg_header('getblocks', block_msg)
    block = block_hdr + block_msg
    Cli.print_msg(block, 'sending')
    s.sendall(block_msg)
    header = s.recv(MSG_HDR_SZ)
    payload_size = Conversion.unmarshal_uint(header[16:20])
    payload = s.recv(payload_size)
    Cli.print_msg(header + payload, 'received')

    Cli.print_msg(block, 'sending')
    s.sendall(block_msg)
    header = s.recv(MSG_HDR_SZ)
    payload_size = Conversion.unmarshal_uint(header[16:20])
    payload = s.recv(payload_size)
    Cli.print_msg(header + payload, 'received')

    Cli.print_msg(block, 'sending')
    s.sendall(block_msg)
    header = s.recv(MSG_HDR_SZ)
    payload_size = Conversion.unmarshal_uint(header[16:20])
    payload = s.recv(payload_size)
    Cli.print_msg(header + payload, 'received')