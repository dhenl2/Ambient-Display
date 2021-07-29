import microphone as mic
import uasyncio as asyncio
import usocket as socket
import utime


async def report_to_system():
    server = '192.168.20.89'
    port = 8123

    async def connect():
        print("Trying to connect to server " + server)
        sock = socket.socket()
        try:
            serv = socket.getaddrinfo(server, port)[0][-1]
            sock.connect(serv)
            print("Connection successful to {} on port {}".format(server, port))
        except OSError as e:
            print('Cannot connect to {} on port {}'.format(server, port))
            sock.close()
        return sock

    def close(sock):
        sock.close()
        print('Server disconnect.')

    def send_msg(sock, writer, msg):
        try:
            print("Sending msg")
            msg += '\0'
            msg = bytes(msg, 'utf-8')
            await writer.awrite(msg)
        except OSError:
            close(sock)

    def receive_msg(sock, reader):
        try:
            msg = await reader.readline()
            msg = msg.decode('utf-8')[:-1]
            print("Received msg: " + msg)
            return msg
        except OSError:
            close(sock)
            return ""

    def perform_handshake(sock, writer, reader):
        sensor = "microphone"
        send_msg(sock, writer, sensor)
        msg = receive_msg(sock, reader)
        if msg != "OK":
            close(sock)

    async def run_program(sock):
        print("Starting running program")
        while True:
            sock_reader = asyncio.StreamReader(sock)
            sock_writer = asyncio.StreamWriter(sock, {})
            perform_handshake(sock, sock_writer, sock_reader)
            while True:
                try:
                    db_reading = get_max_db()
                    send_msg(sock, sock_writer, str(db_reading))
                except OSError:
                    close(sock)
                await asyncio.sleep_ms(0)

    while True:
        conn = await connect()
        await run_program(conn)

def get_max_db():
    # get max dB reading during a 1s or 1000ms period
    max_db = 0
    start_time = utime.ticks_ms()
    while utime.ticks_ms() - start_time < 1000:
        db_reading = mic.read_deb()
        if db_reading > max_db:
            max_db = db_reading
    return max_db

def main():
    report_to_system()

if __name__ == "__main__":
    main()