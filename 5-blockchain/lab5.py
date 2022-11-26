"""


References
(1) version msg -> https://developer.bitcoin.org/reference/p2p_networking.html#version
(2) bitcoin version -> https://developer.bitcoin.org/reference/p2p_networking.html#protocol-versions

"""

import pickle
import socket
from socket import error as socket_error

BUF_SZ = 4096


class Client(object):


    def __init__(self):
        self.host, self.port = 'localhost', 55555
        self.addr = (self.host, self.port)
        self.bitcoin_core_version = 70015

    @property
    def bitcoin_core_version(self):
        """
        The Bitcoin Core protocol network version. By default set to most recent
        version, see reference (2) in the header of this file.
        """
        return self.bitcoin_core_version

    @bitcoin_core_version.setter
    def bitcoin_core_version(self, version):
        self._bitcoin_core_version = version




    def make_version_msg(self):
        """
        Creates the version msg that will be sent to the bitcoin node to init TCP
        handshake. Recipe for version message from reference (1) in the header of this
        file.
        """




if __name__ == '__main__':
    address = ('97.126.42.129', 8333)

    print('blockchain')
    myCli = Client()
    data = myCli.connect(address)
    print(data)