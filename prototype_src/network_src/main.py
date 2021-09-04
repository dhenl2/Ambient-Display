import time
from machine import Pin
try:
  import usocket as socket
except:
  import socket

led = Pin(2, Pin.OUT)

# ========================================================
#           CLIENT
# ========================================================
# https://github.com/peterhinch/micropython-async/blob/master/v2/client_server/uclient.py

import uasyncio as asyncio
import ujson
from heartbeat import heartbeat  # Optional LED flash


async def run():
    server = '192.168.20.89'
    port = 8123

    def connect():
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

    async def send_receive(sock):
        print("Start send/receive messages")
        while True:
            sreader = asyncio.StreamReader(sock)
            swriter = asyncio.StreamWriter(sock, {})
            data = ['value', 1]
            while True:
                try:
                    await swriter.awrite('{}\n'.format(ujson.dumps(data)))
                    res = await sreader.readline()
                except OSError:
                    print("Received OSError")
                    close(sock)
                    return
                await asyncio.sleep(2)
                data[1] += 1

    while True:
        sock_conn = connect()
        await send_receive(sock_conn)


loop = asyncio.get_event_loop()
# Optional fast heartbeat to confirm nonblocking operation
loop.create_task(heartbeat(100))
try:
    loop.run_until_complete(run())
except KeyboardInterrupt:
    print('Interrupted')  # This mechanism doesn't work on Unix build.

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind(('', 80))
# s.listen(5)
#
# while True:
#     conn, addr = s.accept()
#     print('Got a connection from %s' % str(addr))
#     request = conn.recv(1024)
#     request = str(request)
#     print('Content = %s' % request)
#     led_on = request.find('/?led=on')
#     led_off = request.find('/?led=off')
#     if led_on == 6:
#         print('LED ON')
#         led.value(1)
#     if led_off == 6:
#         print('LED OFF')
#         led.value(0)
#     response = web_page()
#     conn.send('HTTP/1.1 200 OK\n')
#     conn.send('Content-Type: text/html\n')
#     conn.send('Connection: close\n\n')
#     conn.sendall(response)
#     conn.close()

# ========================================================
#           SERVER
# ========================================================
# https://github.com/peterhinch/micropython-async/blob/master/v2/client_server/userver.py

# import usocket as socket
# import uasyncio as asyncio
# import uselect as select
# import ujson
# from heartbeat import heartbeat  # Optional LED flash

# class Server:
#     async def run(self, loop, port=8123):
#         addr = socket.getaddrinfo('0.0.0.0', port, 0, socket.SOCK_STREAM)[0][-1]
#         s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # server socket
#         s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         s_sock.bind(addr)
#         s_sock.listen(5)
#         self.socks = [s_sock]  # List of current sockets for .close()
#         print('Awaiting connection on port', port)
#         poller = select.poll()
#         poller.register(s_sock, select.POLLIN)
#         client_id = 1  # For user feedback
#         while True:
#             res = poller.poll(1)  # 1ms block
#             if res:  # Only s_sock is polled
#                 c_sock, _ = s_sock.accept()  # get client socket
#                 loop.create_task(self.run_client(c_sock, client_id))
#                 client_id += 1
#             await asyncio.sleep_ms(200)
#
#     async def run_client(self, sock, cid):
#         self.socks.append(sock)
#         sreader = asyncio.StreamReader(sock)
#         swriter = asyncio.StreamWriter(sock, {})
#         print('Got connection from client', cid)
#         try:
#             while True:
#                 res = await sreader.readline()
#                 if res == b'':
#                     raise OSError
#                 print('Received {} from client {}'.format(ujson.loads(res.rstrip()), cid))
#                 await swriter.awrite(res)  # Echo back
#         except OSError:
#             pass
#         print('Client {} disconnect.'.format(cid))
#         sock.close()
#         self.socks.remove(sock)
#
#     def close(self):
#         print('Closing {} sockets.'.format(len(self.socks)))
#         for sock in self.socks:
#             sock.close()
#
# loop = asyncio.get_event_loop()
# # Optional fast heartbeat to confirm nonblocking operation
# loop.create_task(heartbeat(100))
# server = Server()
# try:
#     loop.run_until_complete(server.run(loop))
# except KeyboardInterrupt:
#     print('Interrupted')  # This mechanism doesn't work on Unix build.
# finally:
#     server.close()
