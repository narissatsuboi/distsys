"""
:file: chord_popuulate.py
:brief: chord_populate takes a port number of an existing node and the filename of the
data file
hashlib: https://docs.python.org/3/library/hashlib.html?highlight=hashlib#module-hashlib
SHA1: https://en.wikipedia.org/wiki/SHA-1
CSV: https://docs.python.org/3/library/csv.html
"""
import csv        # for data parsing
import json       # for nested dict formating
import sys
import hashlib    # for consistent hashing with SHA-1
import array      # to encode prior to hash


class ChordPopulate(object):
    """
    Algo
    Parse all data into dict key : all other data, hash along the way

    """
    def __init__(self, port, filename):
        self.next_port_number, self.file = port, filename
        self.parse_file()


    @staticmethod
    def export_data(d):
        """ Given a dictionary, writes a pretty printed json object to file.
        Used during development to confirm datastore format and key : vals.
        :param d: any dictionary
        :return: file to local directory
        """
        with open('chord_populate_data.json', 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, sort_keys=False, indent=4)
            
    def parse_file(self):
        """
        Creates csv.DictReader object

        :return:
        """

        datastore = {}

        with open(self.file, newline='') as csvfile:
            myReader = csv.DictReader(csvfile)
            columns = myReader.fieldnames
            # print('columns', columns)
            playerId, year = columns[0], columns[3]
            rows = 0
            for row in myReader:
                key = ''.join([row[playerId], row[year]])
                row.pop(playerId, None)
                row.pop(year, None)
                datastore[key] = row

            self.export_data(datastore)


if __name__ == '__main__':
    print('chord_populate.py')
    if len(sys.argv) != 3:
        print('chord_populate.py usage')
        print('python chord_populate.py [existing node port] [filename of data file]')
        exit(1)
    print('running chord populate')
    port, filename = str(sys.argv[1]), sys.argv[2]
    myChordPopulator = ChordPopulate(port, filename)




