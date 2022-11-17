"""
:file: chord_popuulate.py
:brief: chord_populate takes a port number of an existing node and the filename of the
data file
hashlib: https://docs.python.org/3/library/hashlib.html?highlight=hashlib#module-hashlib
SHA1: https://en.wikipedia.org/wiki/SHA-1
CSV: https://docs.python.org/3/library/csv.html
"""
import csv  # for data parsing
import pickle
from datetime import datetime  # for timestamp in log
import hashlib  # for consistent hashing with SHA-1
import json  # for nested dict formating
import socket
import sys

# globals

M = 4  # TODO: Test size, normally hashlib.sha1().digest_size * 8
NODES = 2 ** M  # size of the chord, tot num nodes possible
BUF_SZ = 4096  # socket recv arg
BACKLOG = 100  # socket listen arg
TEST_BASE = 43543  # for testing use port numbers on localhost at TEST_BASE + n


class FileParser(object):
    """
    """

    def __init__(self, file):
        self.file = file
        self.data = {}
        self.parse_and_store_data()

    @staticmethod
    def export_data(d):
        """ Given a dictionary, writes a pretty printed json object to file.
        Used during development to confirm datastore format and key : vals.
        :param d: any dictionary
        :return: file to local directory
        """
        with open('chord_populate_data.json', 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, sort_keys=False, indent=4)

    @staticmethod
    def hash_key(key):
        """ Hashes the key using SHA1 per spec
        :return: hashed key
        """

        digest = hashlib.sha1(str(key).encode()).hexdigest()
        digest = int(digest, 16) % pow(2, M)
        return digest

    def parse_and_store_data(self):  # TODO Handle file reading errors
        """
        Parses rows in self.file, stores in nested dictionary structured per spec, where
        key : value pattern is 'playerid + year' : 'all remaining fields'.
        eg.
        {    unhashed for clarity
            "tomfarris/25138611948": {
                                        "Name": "Farris, Tom",
                                        "Position": "",
                                        "Team": "Chicago Rockets",
                                         ...
                                        "Passer Rating": "0"
                                      }
        }
        """

        # init csv lib object and get column names per spec to use as keys
        with open(self.file, newline='') as csvfile:
            myReader = csv.DictReader(csvfile)
            playerId, year = myReader.fieldnames[0], myReader.fieldnames[3]

            # parse csv by row, store new {k:v} arrangement in self.data
            for row in myReader:
                key = self.hash_key(''.join([row[playerId], row[year]]))
                self.data[key] = row

            # optionally, check the data format is correct
            self.export_data(self.data)

    def get_data(self):
        return self.data


class Chord(object):
    def __init__(self, port, filename):
        self.addr = ('127.0.0.1', 0)
        self.bootstrap_node_addr = ('127.0.01', port)
        self.chord_data = FileParser(filename).get_data()

        self.pr_log('init chord')  # log

    def pr_log(self, msg):
        """Logs Chord's activities"""
        log = '>>> {} | {} | {}'.format(self.addr, msg, datetime.now().timestamp())
        print(log)

    def rpc_send_keys(self):
        """Sends list of all keys to first node to join chord"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            data = sorted(self.chord_data.keys())
            s.connect(('127.0.0.1', 43543))
            s.sendall(pickle.dumps(data))


    def run(self):
        # try to send keys to lone node
        self.rpc_send_keys()

        while True:
            pass
        # TODO, stay alive and work with chord_query.py


if __name__ == '__main__':
    print('//// CHORD POPULATE ////')
    print('>>> Enter first node port and data filepath')
    if len(sys.argv) != 3:
        print('chord_populate.py usage')
        print('python chord_populate.py [existing node port] [filename of data file]')
        exit(1)

    port, filename = int(sys.argv[1]), sys.argv[2]

    chord_client = Chord(port, filename)
    chord_client.run()
