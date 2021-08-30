import time
import socket
import sys
from Server import ServerInfo

class Client:
    def __init__(self, con, server):
        self.sensor = ""
        self.con = con
        self.con.settimeout(10)
        self.name = None
        self.server = server
        self.quit = False
        self.log_file = None
        self.file_date = None
        self.pause = False

    def assign_log_file(self):
        day = time.localtime().tm_mday
        month = time.localtime().tm_mon
        year = time.localtime().tm_year
        today_date = f"{day}-{month}-{year}"
        filename = today_date + "-" + self.sensor + ".csv"
        directory = "Log/"
        file = open(directory + filename, "a")
        return file, today_date

    def check_date(self):
        day = time.localtime().tm_mday
        month = time.localtime().tm_mon
        year = time.localtime().tm_year
        today_date = f"{day}-{month}-{year}"
        if today_date != self.file_date:
            # its now the next day. Start another log file
            self.log_file.close()
            self.log_file, self.file_date = self.assign_log_file()

    def log_to_file(self, msg):
        self.check_date()
        curr_time = "{}:{}:{}".format(
            time.localtime().tm_hour, time.localtime().tm_min, time.localtime().tm_sec)
        if self.sensor == "microphone":
            # logs microphone level received
            data = "{},{}\n".format(curr_time, msg)
        else:
            # logs current people in the area
            people_count = self.server.activity_level.people.get_count()
            data = "{},{}\n".format(curr_time, people_count)
        print(f"{self.name} writing: {data[:-1]}")      # omit /n from print statement
        self.log_file.write(data)

    def receive_input(self):
        msg = self.receive()
        if msg == "" or self.quit:
            self.close()
        return msg

    def __repr__(self):
        return self.name

    def assign_sensor(self, sensor):
        self.sensor = sensor
        self.assign_name(self.server)
        self.log_file, self.file_date = self.assign_log_file()

    def assign_name(self, server):
        print("Assigning name")
        added, client_num = server.add_client(self)
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
                    print(f"Received {buffer} from {self.name}")
                    return buffer
                if len(msg) == 0:
                    break
                buffer += msg
                # print(f"buffer is now {buffer}")
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
        self.log_file.close()
        sys.exit()

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

def add_activity_input(server: ServerInfo, client, new_input):
    if client.sensor == "microphone":
        server.add_mic_input(new_input)
    elif client.sensor == "door_sensor":
        if new_input == "1":
            server.person_entered()
        elif new_input == "-1":
            server.person_left()
        else:
            print("IDK what this is: " + new_input)

def sensor_client(server, client):
    print("Start collecting data")
    msg_queue = []
    while True:
        if client.quit:
            client.close()
        msg = client.receive_input()
        if client.pause:
            # keep receiving messages whilst activity levels are being processed
            msg_queue.append(msg)
        else:
            if len(msg_queue) > 0:
                # empty queue
                for item in msg_queue:
                    add_activity_input(server, client, item)
                    client.log_to_file(item)
                msg_queue = []
            else:
                add_activity_input(server, client, msg)
                client.log_to_file(msg)

def display_client(server, client):
    # ask for new level every 3s
    start = True
    level = 1
    while True:
        time.sleep(3)
        new_level = server.activity_level.get_level()
        client.log_to_file(new_level)
        # send inc/dec from current level to new level
        # on the first command, the initial level is 1 whether its inc/dec
        while level != new_level:
            if level < new_level:
                client.write("inc")
                if start:
                    start = False
                else:
                    level += 1
            elif level > new_level:
                client.write("dec")
                if start:
                    start = False
                else:
                    client -= 1

def client_thread(con, server):
    client = identify_client(con, server)
    if client is None:
        print("closing client")
        return
    if client.sensor == "microphone" or client.sensor == "door_sensor":
        sensor_client(server, client)
    else:
        # display client
        display_client(server, client)

