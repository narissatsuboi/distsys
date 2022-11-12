"""
:file: chord_popuulate.py
:brief: chord_populate takes a port number of an existing node and the filename of the
data file
hashlib: https://docs.python.org/3/library/hashlib.html?highlight=hashlib#module-hashlib
SHA1: https://en.wikipedia.org/wiki/SHA-1
CSV: https://docs.python.org/3/library/csv.html
"""
import csv  # for data parsing
import json  # for nested dict formating
from pathlib import Path  # to check if file exists
import sys
import hashlib  # for consistent hashing with SHA-1


class FileParser(object):
    """
    """

    def __init__(self, file):
        self.file = file
        self.data = {}

    @staticmethod
    def export_data(d):
        """ Given a dictionary, writes a pretty printed json object to file.
        Used during development to confirm datastore format and key : vals.
        :param d: any dictionary
        :return: file to local directory
        """
        with open('chord_populate_data.json', 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, sort_keys=False, indent=4)

    def parse_and_store_data(self):  # TODO Handle file reading errors
        """
        Parses rows in self.file, stores in nested dictionary structured per spec, where
        key : value pattern is 'playerid + year' : 'all remaining fields'.
        eg.
        {
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
                key = ''.join([row[playerId], row[year]])
                row.pop(playerId, None)
                row.pop(year, None)
                self.data[key] = row

            # optionally, check the data format is correct
            self.export_data(self.data)

    def get_data(self):
        return self.data

class Chord(object):
    def __init__(self, filename, port):
        self.first_port = port
        self.chord_data = FileParser(filename).get_data()
        self.node_map = None

    def run(self):
        # init node lookup

        while True:
            pass


if __name__ == '__main__':
    print('//// CHORD POPULATE ////')
    print('>>> Enter new node port and data filepath')
    if len(sys.argv) != 3:
        print('chord_populate.py usage')
        print('python chord_populate.py [existing node port] [filename of data file]')
        exit(1)

    port, filename = str(sys.argv[1]), sys.argv[2]

    chord_client = Chord(port, filename)
