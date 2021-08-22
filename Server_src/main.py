from _thread import *
from Server import start_server, client_thread, ServerInfo
from threading import Lock
import signal

def run_server(server):
    sock = start_server("", 8123)

    while True:
        print(f"Waiting for a connection...")
        con, addr = sock.accept()
        print(f"Connected to {addr}")
        start_new_thread(client_thread, (con, server, ))

def main():
    lock = Lock()
    server = ServerInfo(lock)

    def stop_server(signal_no, frame):
        print("Received signal " + signal_no)
        server.quit_clients()

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGQUIT, stop_server)

    start_new_thread(run_server, (server, ))
    while True:
        pass
    # TODO thread to determine reading to be sent to display based on input


if __name__ == "__main__":
    main()
