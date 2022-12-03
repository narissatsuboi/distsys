"""

:file: lab5.py
:author: Narissa Tsuboi
:date: 12/3/2022
:brief: Connects to BTC HOST, PORT, requests inv from block 0, and searches blocks until
hardcoded block number matches block in inv. Prints matching block hash to console.
Utility classes X for byte transformations and Cli for BTC protocol functions.
References at end of file.
"""

import hashlib
import socket
import time
from socket import error as socket_error
from time import strftime, gmtime

# networking globals
CLI_HOST, CLI_PORT = '127.0.0.1', 59550  # requestor addr
BTC_HOST, BTC_PORT = '95.214.53.160', 8333  # sync node addr
CLI_ADDR, BTC_ADDR = (CLI_HOST, CLI_PORT), (BTC_HOST, BTC_PORT)
MAX_BUF_SZ = 100000  # b

# btc protocol globals
MSG_HDR_SZ = 24  # b
HDR_START, HDR_END = 16, 20
BTC_CORE_VERSION = 70015
MAINNET = 'f9beb4d9'
TIME = int(time.time())
VERSION, VERACK, GETBLOCKS = 'version', 'verack', 'getblocks'
HASH_START, HASH_END, HASH_LEN = 4, 36, 32  # idx for hash retrieval from bytes

# block 0 globals
BTC_HASH_BLOCK_ZERO = bytes.fromhex(
    '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')
BTC_HASH_MERKLE_ROOT = bytes.fromhex(
    '4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b')

# print globals
PAD = ' '
PADD = '  '
HR = '-' * 56  # horizontal rule


class X(object):
    """ Transformation/conversion helper class for byte and unit conversions. All int
    conversions are little endian. """

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
            return X.uint8_t(n)
        if n < 0xffff:
            return X.uint8_t(0xfd) + X.uint16_t(n)
        if n < 0xffffffff:
            return X.uint8_t(0xfe) + X.uint32_t(n)
        return X.uint8_t(0xff) + X.uint64_t(n)

    @staticmethod
    def unmarshal_compactsize(b):
        """
        Converts a compact uint to an uint.
        :param b: bytes or bytearray
        :return: size of bytes, uint
        """
        key = b[0]
        if key == 0xff:
            return b[0:9], X.unmarshal_uint(b[1:9])
        if key == 0xfe:
            return b[0:5], X.unmarshal_uint(b[1:5])
        if key == 0xfd:
            return b[0:3], X.unmarshal_uint(b[1:3])
        return b[0:1], X.unmarshal_uint(b[0:1])

    @staticmethod
    def bool_t(flag):
        """
        Converts bool to 8 bit uint.
        :param flag: bool
        :return: uint8
        """
        return X.uint8_t(1 if flag else 0)

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
    """
    Utility class to find a btc block starting search from block 0. Utilizes TCP/IP
    secure communication.
    """

    """ MAKE HEADER OR MESSAGE ------------------------------------------------------ """

    @staticmethod
    def make_package(command):
        """
        Forms a header and message (if required) based off of the command. Combines
        into byte array.
        :param command: a btc protocol command ie 'version'
        :return: bytes or byte array representing header and message
        """
        msg = ''
        if command == VERSION or command == GETBLOCKS:
            if command == VERSION:
                msg = Cli.make_version_msg()
            elif command == GETBLOCKS:
                msg = Cli.make_getblocks_msg()
            hdr = Cli.make_msg_header(command, msg)
            return hdr + msg
        elif command == VERACK:
            hdr = Cli.make_msg_header(command)
            return hdr

    @staticmethod
    def make_msg_header(command, b=None):
        """
        Determines header params and converts to bytes. Returns byte str of header
        information.
        :param command: bitcoin command to send to node
        :param b: byte str or byte array
        """
        CMD_MAX_LEN = 12  # byte len of encoded command

        if b is None:  # header only
            b = ''.encode()

        start_string = bytearray.fromhex(MAINNET)  # origin network

        if len(command) < CMD_MAX_LEN:  # protocol command, padded
            command += ('\0' * (CMD_MAX_LEN - len(command)))

        return start_string + command.encode() + X.uint32_t(len(b)) + Cli.checksum(b)

    @staticmethod
    def make_block_header():
        """
        Makes block header
        """
        block_version = X.int32_t(4)
        prev_block_header_hash = BTC_HASH_BLOCK_ZERO
        merkle_root_hash = prev_block_header_hash
        time = X.uint32_t(TIME)
        nbits = X.uint32_t(0)
        nonce = X.uint32_t(0)
        block_header_hash = block_version + prev_block_header_hash + merkle_root_hash + time + nbits \
                            + nonce
        return block_header_hash

    @staticmethod
    def make_version_msg():
        """
        Makes the version msg that will be sent to the bitcoin node.
        :return: version message in bytes
        """

        ver = X.int32_t(BTC_CORE_VERSION)  # my protocol
        services = X.uint64_t(0)  # my services (none)
        timestamp = X.int64_t(int(time.time()))  # my unix epoch time
        addr_recv_services = X.uint64_t(1)  # host services (full node)
        addr_recv_ip_addr = X.ipv6_from_ipv4(BTC_HOST)  # host's addr IPv6
        addr_recv_port = X.uint16_t(BTC_PORT)  # host's port
        addr_trans_services = services  # addr_trans servs
        addr_trans_ip_addr = X.ipv6_from_ipv4(CLI_HOST)  # my IPv6
        addr_trans_port = X.uint16_t(CLI_PORT)  # my port
        nonce = X.uint64_t(0)  # nonce
        user_agent_bytes = X.compactsize_t(0)  # user_agent_bytes -> 0
        start_height = X.int32_t(0)  # start_height -> 0
        relay = X.bool_t(False)  # relay -> False

        version_msg = ver + services + timestamp + addr_recv_services + \
                      addr_recv_ip_addr + addr_recv_port + addr_trans_services + \
                      addr_trans_ip_addr + addr_trans_port + nonce + user_agent_bytes + \
                      start_height + relay

        return version_msg

    @staticmethod
    def make_getblocks_msg():
        """
        Makes getblocks protocol message, used to request an 'inv' msg from BTC node.
        :returns: inv msg in bytes
        """

        ver = X.uint32_t(BTC_CORE_VERSION)  # my protocol
        hashcount = X.compactsize_t(1)  # count hashes I know
        hdr_hashes = X.swap_endianness(BTC_HASH_BLOCK_ZERO)  # hashes I know
        stop_hash = bytearray(32)  # get 500 back

        return ver + hashcount + hdr_hashes + stop_hash

    @staticmethod
    def parse_inv_bytes_to_hash(b):
        """
        Expects bytes from inventory message less header with 500 block hashes.
        :return: list of hashes contained in byte payload.
        """
        hashes = []  # holds hashes collected from b in bytes

        # skip count expressed bytes (offset), update offset
        count_invs_b, count_inv_int = X.unmarshal_compactsize(b)
        offset = len(count_invs_b)

        # parse byte array, store hashes
        for i in range(count_inv_int):
            hashes.append(b[offset + HASH_START: offset + HASH_END])
            offset += HASH_END
        return hashes

    """ UTILS ----------------------------------------------------------------------- """

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
    def parse_bytes_recv(b):
        """
        Parses byte stream and separates byte messages. Returns list of byte messages.
        :param b: bytes or bytearray
        :return: list of bytearrays
        """

        msgs_recv = []
        while len(b) > 0:
            # get the size of this payload from header
            payload_sz = X.unmarshal_uint(b[HDR_START:HDR_END])
            msg_len = payload_sz + MSG_HDR_SZ

            # grab the bytes from start to msg_len
            msg = b[:msg_len]
            msgs_recv.append(msg)
            b = b[msg_len:]

        return msgs_recv

    """ NETWORKING ------------------------------------------------------------------ """

    @staticmethod
    def send_and_receive_bytes(sock, b):
        """
        Sends bytes on given socket, receives bytestream response and returns it.
        :param sock: socket connected to host
        :param b: bytes or byte array to send
        :return: bytes received
        """
        recv_bytes = bytearray()
        sock.settimeout(1.5)
        try:
            sock.sendall(b)
            while True:
                recv_bytes += sock.recv(MAX_BUF_SZ)
        except socket_error as serr:
            pass

        return recv_bytes

    """ PRINT ----------------------------------------------------------------------- """

    @staticmethod
    def print_msg(msg, text='', start=1, end=500):
        """
        Prints msgs custom to BTC command embedded in msg payload.
        inv command returns list of block hashes.
        :param msg: payload in bytes
        :param text: text to display in console for this msg
        :param start: start block number for inv command
        :param end: end block number for inv command
        """
        print('\n{}MESSAGE'.format('' if text is None else (text + ' ')))
        print('({}) {}'.format(len(msg), msg[:60].hex() + ('' if len(msg) < 60 else
                                                           '...')))
        payload = msg[MSG_HDR_SZ:]  # extract payload

        # print header
        command = Cli.print_header(msg[:MSG_HDR_SZ], Cli.checksum(payload))

        # print msg customized by command
        if command == 'version':
            Cli.print_version_msg(payload)
        elif command == 'getblocks':
            Cli.print_getblocks(payload)
        elif command == 'inv':
            return Cli.print_inv_msg(payload, start, end)

    @staticmethod
    def print_version_msg(b):
        """
        Prints formatted list of version_msg, bytes shown in hex.
        :param b: payload from make_version_msg
        """
        global PAD

        # extract  fields
        version, my_services, epoch_time, your_services = b[:4], b[4:12], b[12:20], \
                                                          b[20:28]
        rec_host, rec_port, my_services2, my_host, my_port = b[28:44], b[44:46], \
                                                             b[46:54], b[54:70], \
                                                             b[70:72]
        nonce = b[72:80]
        user_agent_size, uasz = X.unmarshal_compactsize(b[80:])
        i = 80 + len(user_agent_size)
        user_agent = b[i:i + uasz]
        i += uasz
        start_height, relay = b[i:i + 4], b[i + 4:i + 5]
        extra = b[i + 5:]

        # print report
        PAD = '  '
        print(PAD + 'VERSION')
        print(PADD + HR)
        PAD *= 2
        print('{}{:32} version {}'.format(PAD, version.hex(),
                                          X.unmarshal_int(version)))
        print('{}{:32} my services'.format(PAD, my_services.hex()))
        time_str = strftime("%a, %d %b %Y %H:%M:%S GMT",
                            gmtime(X.unmarshal_int(epoch_time)))
        print('{}{:32} epoch time {}'.format(PAD, epoch_time.hex(), time_str))
        print('{}{:32} your services'.format(PAD, your_services.hex()))
        print(
            '{}{:32} your host {}'.format(PAD, rec_host.hex(),
                                          X.ipv6_to_ipv4(rec_host)))
        print('{}{:32} your port {}'.format(PAD, rec_port.hex(),
                                            X.unmarshal_uint(rec_port)))
        print('{}{:32} my services (again)'.format(PAD, my_services2.hex()))
        print('{}{:32} my host {}'.format(PAD, my_host.hex(),
                                          X.ipv6_to_ipv4(my_host)))
        print('{}{:32} my port {}'.format(PAD, my_port.hex(),
                                          X.unmarshal_uint(my_port)))
        print('{}{:32} nonce'.format(PAD, nonce.hex()))
        print('{}{:32} user agent size {}'.format(PAD, user_agent_size.hex(), uasz))
        print('{}{:32} user agent \'{}\''.format(PAD, user_agent.hex(),
                                                 str(user_agent, encoding='utf-8')))
        print('{}{:32} start height {}'.format(PAD, start_height.hex(),
                                               X.unmarshal_uint(start_height)))
        print('{}{:32} relay {}'.format(PAD, relay.hex(), bytes(relay) != b'\0'))
        if len(extra) > 0:
            print('{}{:32} EXTRA!!'.format(PAD, extra.hex()))

    @staticmethod
    def print_header(header, expected_cksum=None):
        """
        Report the contents of the given bitcoin message header
        :param header: bitcoin message header (bytes or bytearray)
        :param expected_cksum: the expected checksum for this version message, if known
        :return: command type
        """

        global PADD
        magic, command_hex, payload_size, cksum = header[:4], header[4:16], header[
                                                                            16:20], header[
                                                                                    20:]
        command = str(bytearray([b for b in command_hex if b != 0]), encoding='utf-8')
        psz = X.unmarshal_uint(payload_size)
        if expected_cksum is None:
            verified = ''
        elif expected_cksum == cksum:
            verified = '(verified)'
        else:
            verified = '(WRONG!! ' + expected_cksum.hex() + ')'
        PADD = '  '
        print(PADD + 'HEADER')
        print(PADD + HR)
        PADD *= 2
        print('{}{:32} magic'.format(PADD, magic.hex()))
        print('{}{:32} command: {}'.format(PADD, command_hex.hex(), command))
        print('{}{:32} payload size: {}'.format(PADD, payload_size.hex(), psz))
        print('{}{:32} checksum {}'.format(PADD, cksum.hex(), verified))
        return command

    @staticmethod
    def print_getblocks(b):
        """
        Prints getblocks message.
        :param b: get_blocks msg in bytes
        """

        global PADD
        ver, count, header_hash, stop_hash = b[:4], b[4:5], b[5:37], b[37:]
        # version, count, header_hash, stop_hash = b[:4], b[4:8], b[8:40], b[40:]

        print(PADD + 'GETBLOCKS')
        print(PADD + HR)
        print('{}{:32} version {}'.format(PADD, ver.hex(), X.unmarshal_int(ver)))
        print('{}{:32} hashcount {}'.format(PADD, count.hex(),
                                            X.unmarshal_compactsize(count)[1]))
        print('{}{:32} header hash'.format(PADD, header_hash.hex()[:HASH_LEN]))
        print('{}{:32} stop hash'.format(PADD, stop_hash.hex()[:HASH_LEN]))

    @staticmethod
    def print_inv_msg(b, start=0, end=500):
        """
        Prints inv message and returns list of hashes.
        :param b: inv_msg in bytes
        :param start: start block number for inv command
        :param end: end block number for inv command
        """

        global PADD
        hashes = Cli.parse_inv_bytes_to_hash(b)

        # parse hashes, skip count in bytes (offset)
        count_b, count = X.unmarshal_compactsize(b)
        hash_len = 32
        print('{}{}{}{}'.format(PADD, 'INV - requested ', count, ' inventories'))
        print(PADD + HR)
        for hash in hashes:
            hash_hex = X.swap_endianness(hash).hex()
            row_1, row_2 = hash_hex[:hash_len], hash_hex[hash_len:]
            start += 1
            print('{}{}\n{}{} block {} / {}'.format(PADD, row_1, PADD, row_2,
                                                    start, end))
        return hashes

    @staticmethod
    def print_my_block(b, block_num):
        """
        Prints my block hash.
        :param b: hash of block in bytes
        :param block_num: block number, int
        """
        print()
        print(PAD + HR)
        print(PAD + HR)
        print('{}BLOCK {} FOUND!'.format(PAD, my_block))
        print(PAD + HR)
        print(X.swap_endianness(b).hex())
        print(PAD + HR)


if __name__ == '__main__':
    """
    Connects to BTC HOST, PORT, requests inv from block 0, and searches blocks until 
    hardcoded block number matches block in inv. Prints matching block hash to console. 
    """

    # init client
    my_block = 1697482 % 10000  # 7482
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BTC_HOST, BTC_PORT))

    # send version, recv version and verack
    version = Cli.make_package(VERSION)
    Cli.print_msg(version, 'sending')
    msgs = Cli.parse_bytes_recv(Cli.send_and_receive_bytes(s, version))
    for msg in msgs:
        Cli.print_msg(msg, 'received')

    # send verack (hdr only)
    verack = Cli.make_package(VERACK)
    Cli.print_msg(verack, 'sending')
    # will include sendheaders, sendcmpctx2, ping, feefilter
    msgs = Cli.parse_bytes_recv(Cli.send_and_receive_bytes(s, verack))
    for msg in msgs:
        Cli.print_msg(msg, 'received')

    # send getblocks get inv
    # keep searching for block num until found
    hashes = []
    blocks_seen, block_total = 0, 500
    while blocks_seen <= my_block:
        getblocks = Cli.make_package(GETBLOCKS)
        Cli.print_msg(getblocks, 'sending')
        msgs = Cli.parse_bytes_recv(Cli.send_and_receive_bytes(s, getblocks))
        for msg in msgs:
            hashes = Cli.print_msg(msg, 'received', blocks_seen, block_total)
        blocks_seen = block_total
        block_total += 500

    # retrieve the hash and print to console
    my_block_hash = hashes[(my_block % 500) - 1]
    Cli.print_my_block(my_block_hash, my_block)

"""
References
header - > https://github.com/nfj5/Distributed-Systems-CPSC5520-FQ19/blob/ddf90183ef6b4da09059af4c137e6004c8f49219/Lab5/lab5.py#L185
version msg -> https://developer.bitcoin.org/reference/p2p_networking.html#version
bitcoin version -> https://developer.bitcoin.org/reference/p2p_networking.html#protocol-versions
byte conversion -> https://docs.python.org/3/library/stdtypes.html#int.from_bytes,
https://docs.python.org/3/library/stdtypes.html#int.to_bytes
Max BTC buffer size -> https://github.com/nfj5/Distributed-Systems-CPSC5520-FQ19/blob
/ddf90183ef6b4da09059af4c137e6004c8f49219/Lab5/lab5.py#L185
getblocks -> https://developer.bitcoin.org/reference/p2p_networking.html#getblocks
compactuint -> https://btcinformation.org/en/developer-reference#compactsize
-unsigned-integers
block header -> https://btcinformation.org/en/developer-reference#compactsize-unsigned-integers
block zero -> https://en.bitcoin.it/wiki/Genesis_block
swap endian -> https://www.folkstalk.com/2022/10/python-little-endian-to-big-endian-with
-code-examples.html
"""