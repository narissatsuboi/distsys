from lab5 import Client

if __name__ == "__main__":
    cli = Client()
    checksum = '0x5df6e0e2'
    print(checksum.encode())
    # print(cli.double_sha256(''.encode())[0:4].hex())
