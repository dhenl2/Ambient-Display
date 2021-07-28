from _thread import *
from Server import start_server, client_thread, ServerInfo
from threading import Lock

def run_server(clients):
    sock = start_server("", 8123)
    lock = Lock()
    server = ServerInfo(lock)
    while True:
        print(f"Waiting for a connection...")
        con, addr = sock.accept()
        print(f"Connected to {addr}")
        start_new_thread(client_thread, (con, clients, server, ))
        # command = input("Input command: ")
        # command += '\n'
        # con.send(bytes(command, 'utf-8'))
        # result = con.recv(1024)
        # print("Received : " + str(result.decode("utf-8")))


def main():
    # clients = microphone, door_sensor, display
    clients = list(), list(), list()
    start_new_thread(run_server, (clients, ))
    # TODO thread to determine reading to be sent to display based on input




if __name__ == "__main__":
    main()
