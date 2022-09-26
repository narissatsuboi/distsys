""""
CPSC 5520, Seattle University
This is free and unencumbered software released into the public domain.
:Authors: Narissa Tsuboi
:Version: 1
"""
import socket
import sys

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("Client Main")

    if len(sys.argv) != 3:
        print("Usage: python lab1.py HOST PORT")
        exit(1);

    host = sys.argv[1]
    port = int(sys.argv[2])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(b'JOIN')
        data = s.recv(1024)
    print('Received', repr(data))
