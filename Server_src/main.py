from _thread import *
from Server import start_server, client_thread, ServerInfo
from threading import Lock

def run_server():
    sock = start_server("", 8123)
    lock = Lock()
    server = ServerInfo(lock)
    while True:
        print(f"Waiting for a connection...")
        con, addr = sock.accept()
        print(f"Connected to {addr}")
        start_new_thread(client_thread, (con, server, ))

def main():
    start_new_thread(run_server, ())
    while True:
        pass
    # TODO thread to determine reading to be sent to display based on input
    # TODO add signal handler for SIGKILL/SIGINT to close all files


if __name__ == "__main__":
    main()
