import microphone as mic
import uasyncio as asyncio
import usocket as socket
import utime

async def report_to_system():
    server = '192.168.7.1'
    port = 8123

    async def connect():
        print("Trying to connect to server " + server)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        sensor = "microphone"
        await send_msg(sock, writer, sensor)
        msg = await receive_msg(sock, reader)
        if msg != "Received":
            close(sock)

    async def run_program(sock):
        print("Starting running program")
        while True:
            sock_reader = asyncio.StreamReader(sock)
            sock_writer = asyncio.StreamWriter(sock, {})
            await perform_handshake(sock, sock_writer, sock_reader)
            while True:
                db_reading = await get_max_db(1)
                print(str(db_reading) + "dB")
                result = await send_msg(sock, sock_writer, str(db_reading))
                if not result:
                    return
                # await receive msg
                await receive_msg(sock, sock_reader)
                await asyncio.sleep_ms(0)

    while True:
        con = await connect()
        while con is None:
            con = await connect()
        await run_program(con)

async def get_max_db(period):
    # get max dB reading during a specified period (s)
    max_db = 0
    start_time = utime.ticks_ms()
    while utime.ticks_ms() - start_time < (period * 1000):
        db_reading = mic.read_deb()
        if db_reading > max_db:
            max_db = db_reading
    return max_db

def test():
    while True:
        print("dB reading: " + str(mic.read_deb()) + "dB")
        utime.sleep(1)

def main():
    asyncio.run(report_to_system())
    # test()

if __name__ == "__main__":
    main()
