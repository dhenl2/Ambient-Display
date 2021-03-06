import time
import display as dp
from machine import Pin
import uasyncio as asyncio
from uasyncio import Lock
import network
try:
    import usocket as socket
except:
    import socket


class UserInput:
    def __init__(self, lock):
        self.read = None
        self.lock = lock

    async def read_input(self):
        # print("reading user input")
        await self.lock.acquire()
        result = self.read
        self.lock.release()
        # print("finished reading user input")
        return result

    async def add_input(self, new_input):
        print("adding user input")
        await self.lock.acquire()
        self.read = new_input
        self.lock.release()
        print("finished adding user input")

    async def reset_input(self):
        await self.lock.acquire()
        self.read = None
        self.lock.release()

async def read_user_input(user):
    while True:
        # val = await ainput("Choose to (inc, dec): ")
        if val != "inc" or val != "dec":
            print("Not a valid input")
        else:
            user.add_input(val)
        await asyncio.sleep(2)


async def pretend_user_input(user):
    print("Pretending to be a user")
    user_inputs = ['inc', 'inc', 'inc', 'inc', 'inc', 'inc', 'dec', 'dec', 'dec', 'dec', 'dec']
    from display import Time
    timer = Time()
    timer.start_timer()
    while True:
        for i in range(len(user_inputs)):
            print("Adding user input " + user_inputs[i])
            await user.add_input(user_inputs[i])
            await asyncio.sleep(30)
        print("Finished adding user inputs")


async def read_external_input(user):
    server = '192.168.7.1'
    port = 8123

    async def connect():
        print("Trying to connect to server " + server)
        sock = socket.socket()
        try:
            serv = socket.getaddrinfo(server, port)[0][-1]
            sock.connect(serv)
            print("Connection successful to {} on port {}".format(server, port))
            return sock
        except OSError as e:
            print('Cannot connect to {} on port {}'.format(server, port))
            sock.close()
            return None

    def close(sock):
        sock.close()
        print('Server disconnect.')

    async def send_msg(sock, writer, msg):
        try:
            print("Sending msg")
            msg += '\n'
            msg = bytes(msg, 'utf-8')
            await writer.awrite(msg)
            return True
        except OSError:
            close(sock)
            return False

    async def receive_msg(sock, reader):
        try:
            msg = await reader.readline()
            msg = msg.decode('utf-8')[:-1]
            print("Received msg: " + msg)
            return msg
        except OSError:
            close(sock)
            return ""

    async def perform_handshake(sock, writer, reader):
        print("Performing handshake")
        sensor = "display"
        await send_msg(sock, writer, sensor)
        msg = await receive_msg(sock, reader)
        if msg != "Received":
            close(sock)

    async def run_program(sock):
        print("Start running program")
        while True:
            sock_reader = asyncio.StreamReader(sock)
            sock_writer = asyncio.StreamWriter(sock, {})
            await perform_handshake(sock, sock_writer, sock_reader)
            while True:
                command = await receive_msg(sock, sock_reader)
                if command == "":
                    return
                await user.add_input(command)
                await asyncio.sleep_ms(0)

    while True:
        con = await connect()
        while con is None:
            con = await connect()
        await run_program(con)


async def main():
    time.sleep(2)
    print("Starting main()")
    dp_pin = Pin(13)  # adjust plz
    user = UserInput(Lock())
    loop = asyncio.get_event_loop()
    loop.create_task(dp.animation_idea_1(dp_pin, user))
    loop.create_task(read_external_input(user))
    loop.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
