"""
:file: chord_popuulate.py
:brief: chord_populate takes a port number of an existing node and the filename of the
data file
"""
import sys
import hashlib    # for consistent hashing with SHA-1

class ChordPopulate(object):
    """
    Algo
    Parse all data into dict key : all other data, hash along the way

    """




if __name__ == '__main__':
    print('chord_populate.py')
    if len(sys.argv) != 3:
        print('chord_populate.py usage')
        print('python chord_populate.py [existing node port] [filename of data file]')
        exit(1)
    print('running chord populate')
    port, filename = int(sys.argv[1]), sys.argv[2]
    print(port, filename)
