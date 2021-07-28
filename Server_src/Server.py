import socket
import time

class ServerInfo:
    def __int__(self, lock):
        self.count = 0
        self.lock = lock

    def add_count(self, amount):
        self.lock.acquire()
        self.count += amount
        self.lock.release()

class Client:
    def __init__(self, sensor, con, clients):
        self.sensor = sensor
        self.con = con
        self.name = None
        self.assign_name(clients)

    def assign_name(self, clients):
        check_clients = None
        if self.sensor == "microphone":
            check_clients = clients[0]
        elif self.sensor == "door_sensor":
            check_clients = clients[1]
        elif self.sensor == "display":
            check_clients = clients[2]
        else:
            # invalid sensor name
            self.name = "invalid"

        if check_clients is not None:
            check_clients.append(self)
            self.name = f"{self.sensor} ({len(check_clients)})"

    def write(self, msg):
        try:
            self.con.send(bytes(msg + "\n", 'utf-8'))
        except OSError:
            self.close()

    def receive(self):
        # all sent messages are expected to end with a null character
        try:
            msg = self.con.recv(1024).decode('utf-8')
            msg = msg[:-1]      # remove \0
            return msg
        except OSError:
            self.close()
            return ""

    def close(self):
        print(f"{self.name} has disconnected. Severing connection")
        self.con.close()

def start_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
    except socket.error as e:
        print(f"Failed to bind. Received error:\n{e}")
        exit(1)
    sock.listen(5)
    print(f"Listening on {socket.gethostbyname(socket.gethostname())}")
    return sock

def identify_client(con, clients):
    con.send(bytes("WHO:", 'utf-8'))
    # area, sensor
    identification = con.recv(1024).decode('utf-8')
    sensor = identification[:-1]
    return Client(sensor, con, clients)



def client_thread(con, clients, server):
    client = identify_client(con, clients)
    if client.sensor == "microphone":
        file = open("microphone.csv", "a")
        while True:
            msg = client.receive()
            if msg == "":
                # client has disconnected
                return
            file.write(f"{msg},{time.time()}\n")
    elif client.sensor == "door_sensor":
        file = open("door_sensor.csv", "a")
        while True:
            msg = client.receive()
            if msg == "":
                # client has disconnected
                return
            msg = int(msg)
            server.add_count(msg)
            file.write(f"{msg},{time.time()}\n")
    elif client.sensor == "display":
        # TODO after interpreting average of results
        pass
    else:
        # invalid input
        return