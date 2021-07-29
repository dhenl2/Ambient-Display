import socket
import time
import select

class ServerInfo:
    def __init__(self, lock):
        self.count = 0
        self.lock = lock
        self.display_clients = list()
        self.microphone_clients = list()
        self.door_sensor_clients = list()

    def add_count(self, amount):
        self.lock.acquire()
        self.count += amount
        self.lock.release()

    def add_client(self, sensor, client):
        num = 0
        if sensor == "microphone":
            print("Adding microphone client")
            self.microphone_clients.append(client)
            num = len(self.microphone_clients)
        elif sensor == "door_sensor":
            print("Adding door_sensor client")
            self.door_sensor_clients.append(client)
            num = len(self.door_sensor_clients)
        elif sensor == "display":
            print("Adding display client")
            self.display_clients.append(client)
            num = len(self.display_clients)
        else:
            return False, 0
        return True, num

    def remove_client(self, client):
        print("Removing client")
        clients = None
        if client.sensor == "microphone":
            clients = self.microphone_clients
        elif client.sensor == "door_sensor":
            clients = self.door_sensor_clients
        elif client.sensor == "display":
            clients = self.display_clients
        else:
            # server does not keep track of invalid clients
            return

        for i in range(len(clients)):
            if clients[i] == client:
                # found same client
                removed_client = clients.pop(i)
                print(f"Removed client: {removed_client}")

class Client:
    def __init__(self, con, server):
        self.sensor = ""
        self.con = con
        self.con.settimeout(10)
        self.name = None
        self.server = server

    def __repr__(self):
        return self.name

    def assign_sensor(self, sensor):
        self.sensor = sensor
        self.assign_name(self.server)

    def assign_name(self, server):
        print("Assigning name")
        added, client_num = server.add_client(self.sensor, self)
        if added:
            self.name = f"{self.sensor} ({client_num})"
        else:
            # invalid sensor name
            self.name = "invalid"
        print("Client assigned name: " + self.name)

    def write(self, msg):
        try:
            print("Writing msg: " + msg)
            self.con.send(bytes(msg + "\n", 'utf-8'))
        except OSError:
            self.close()

    def receive(self):
        print("Receiving msg")
        # all sent messages are expected to end with a \n
        buffer = ""
        timeout_count = 0
        while True:
            try:
                msg = self.con.recv(1).decode('utf-8')
                if msg == "\n":
                    # once a message has been read, a "received" message is sent for confirmation
                    self.write("Received")
                    return buffer
                buffer += msg
                print(f"buffer is now {buffer}")
            except socket.timeout:
                print("Hit socket timeout")
                timeout_count += 1
                if timeout_count >= 5:
                    self.close()
                    return ""
                continue
            except socket.error:
                self.close()
                return ""

    def close(self):
        print(f"{self.name} has disconnected. Severing connection")
        self.con.close()
        self.server.remove_client(self)

def start_server(host, port):
    print("Starting server")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
    except socket.error as e:
        print(f"Failed to bind. Received error:\n{e}")
        exit(1)
    sock.listen(5)
    print(f"Listening on {socket.gethostbyname(socket.gethostname())}")
    return sock

def identify_client(con, server):
    print("Identifying new client")
    new_client = Client(con, server)
    sensor = new_client.receive()
    new_client.assign_sensor(sensor)
    if new_client.name != "invalid":
        new_client.write("OK")
        return new_client
    else:
        return None

def log_to_file(file, client):
    while True:
        msg = client.receive()
        if msg == "":
            print("Closing file")
            file.close()
            return
        data = "{},{}\n".format(msg, time.time())
        print("Writing: " + data)
        file.write(data)

def client_thread(con, server):
    client = identify_client(con, server)
    if client is None:
        return
    print("Start logging")
    if client.sensor == "microphone":
        print("logging to microphone.csv")
        file = open("microphone.csv", "a")
        log_to_file(file, client)
    elif client.sensor == "door_sensor":
        file = open("door_sensor.csv", "a")
        log_to_file(file, client)
    elif client.sensor == "display":
        # TODO after interpreting average of results
        pass
    else:
        # invalid input
        return