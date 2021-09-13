import socket
import time

from ActivityLevel import *

class ServerInfo:
    def __init__(self, lock):
        self.count = 0
        self.lock = lock
        self.display_clients = list()
        self.microphone_clients = list()
        self.door_sensor_clients = list()
        self.activity_level = ActivityLevel(self)
        self.threads = []
        self.calibrate_now = False
        self.stop_displays = False

    def quit_clients(self):
        clients = [self.display_clients, self.microphone_clients, self.door_sensor_clients]
        for client in clients:
            for sub_client in client:
                sub_client.quit = True

    def add_count(self, amount):
        self.lock.acquire()
        self.count += amount
        self.lock.release()

    def set_display_clients(self, value):
        print(len(self.display_clients))
        self.stop_displays = value
        if len(self.display_clients) > 0:
            for client in self.display_clients:
                client.pause = value

    def add_client(self, client):
        num = 0
        if client.sensor == "microphone":
            print("Adding microphone client")
            self.microphone_clients.append(client)
            num = len(self.microphone_clients)
        elif client.sensor == "door_sensor":
            print("Adding door_sensor client")
            self.door_sensor_clients.append(client)
            num = len(self.door_sensor_clients)
        elif client.sensor == "display":
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

        if client in clients:
            index = clients.index(client)
            clients.pop(index)
    
    def set_clients_pause(self, value):
        clients = [self.door_sensor_clients, self.microphone_clients]
        for client_type in clients:
            for client in client_type:
                client.pause = value
    
    def person_entered(self):
        self.lock.acquire()
        self.activity_level.people.add_person()
        self.lock.release()
    
    def person_left(self):
        self.lock.acquire()
        self.activity_level.people.remove_person()
        self.lock.release()
    
    def add_mic_input(self, new_input):
        self.lock.acquire()
        self.activity_level.add_mic_input(new_input)
        self.lock.release()

def start_server(host, port):
    print("Starting server")
    connected = False
    sock = None
    while not connected:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
            connected = True
        except socket.error as e:
            print(f"Failed to bind. Received error:\n{e}")
            sock.close()
            time.sleep(3)
    sock.listen(5)
    print(f"Listening on {socket.gethostbyname(socket.gethostname())}")
    return sock

