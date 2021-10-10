from door_sensor import Time, Sensor, check_for_passers, thread_get_distance
import uasyncio as asyncio
from uasyncio import Lock
import gc
from hcsr04 import HCSR04
import utime
import usocket as socket
import network

async def write_data(file, left_sensor, right_sensor, time, header=False):
    left_distance = right_distance = None
    if left_sensor.distance is not None:
        left_distance = left_sensor.distance
    if right_sensor.distance is not None:
        right_distance = right_sensor.distance

    # Check if distance is invalid
    if left_distance is None:
        left_distance = ""
    else:
        left_distance = int(left_distance)

    if right_distance is None:
        right_distance = ""
    else:
        right_distance = int(right_distance)

    data = str(time.get_elapsed()) + "," + str(left_sensor.average) + "," + str(left_distance) + "," + \
           str(right_sensor.average) + "," + str(right_distance) + "\n"
    if header:
        file.write("time (s),Left (avg),Left,Right (avg),Right\n")
    file.write(data)

async def record_log(duration, frequency, sensor_left, sensor_right, lock):
    # record distance
    file = open("record.csv", "w")
    print("Starting Recording Session at " + str(frequency) + "Hz")
    count = 0
    time = Time(utime.ticks_ms())
    time.start_time = utime.ticks_ms()
    time.prev_time = time.start_time
    while time.get_elapsed() < duration:
        await asyncio.sleep_ms(0)
        if time.get_dt() > (1 / frequency):
            # show progress
            if count != 0 and count % 100 == 0:
                percentage = float(count) / 10
                percentage = str(percentage)
                print("{0}% @ {1}s".format(str(percentage), time.get_elapsed()))
                # print(percentage + "% @ " + time.get_elapsed() + "s")

            await check_for_passers(sensor_left, sensor_right, lock)
            if count == 0:
                await write_data(file, sensor_left, sensor_right, time, header=True)
            else:
                await write_data(file, sensor_left, sensor_right, time)
            time.prev_time = utime.ticks_ms()
            count += 1
    file.close()
    print("Ending Recording Session")
    return

async def report_to_system(sensor_left, sensor_right, lock):
    server = '192.168.7.1'
    port = 8123

    async def connect_wifi():
        print("Connecting to WIFI")
        ssid = 'AmbientDisplay'
        password = 'Password.1'
        station.connect(ssid, password)
        while not station.isconnected():
            pass

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
        sensor = "door_sensor"
        await send_msg(sock, writer, sensor)
        msg = await receive_msg(sock, reader)
        if msg != "Received":
            close(sock)

    async def run_program(sock):
        print("Starting running program")
        connection_timer = 5
        timer = Time(utime.ticks_ms())
        while True:
            sock_reader = asyncio.StreamReader(sock)
            sock_writer = asyncio.StreamWriter(sock, {})
            await perform_handshake(sock, sock_writer, sock_reader)
            while True:
                result = await check_for_passers(sensor_left, sensor_right, lock, True)
                if result is None and timer.get_elapsed() > connection_timer:
                    # send response to maintain connection
                    result = await send_msg(sock, sock_writer, "empty")
                    if not result:
                        return
                    await receive_msg(sock, sock_reader)
                    timer.start_time = utime.ticks_ms()
                elif result is not None:
                    result = await send_msg(sock, sock_writer, str(result))
                    if not result:
                        return
                    await receive_msg(sock, sock_reader)
                await asyncio.sleep_ms(0)

    station = network.WLAN(network.STA_IF)
    station.active(True)
    while True:
        if not station.isconnected():
            print("WIFI not connected")
            await connect_wifi()
        print("WIFI is connected")
        con = await connect()
        while con is None:
            con = await connect()
        await run_program(con)

async def main():
    print("Starting main()")
    garbage = gc
    frequency = 30 # hz
    lock = Lock()
    sensor_left = Sensor(HCSR04(trigger_pin=14, echo_pin=12), "left", lock)
    sensor_right = Sensor(HCSR04(trigger_pin=5, echo_pin=4), "right", lock)

    sensor_left.calibrate(frequency, 10)
    sensor_right.calibrate(frequency, 10)
    garbage.collect()
    garbage.enable()

    # threads
    loop = asyncio.get_event_loop()
    loop.create_task(thread_get_distance(sensor_left, frequency))
    loop.create_task(thread_get_distance(sensor_right, frequency))
    # loop.run_until_complete(record_log(30, 30, sensor_left, sensor_right, lock))
    loop.run_until_complete(report_to_system(sensor_left, sensor_right, lock))
    print("Leaving main()")
    return

def test():
    sensor_left = HCSR04(trigger_pin=14, echo_pin=12)
    sensor_right = HCSR04(trigger_pin=5, echo_pin=4)
    while True:
        print("Left: " + str(sensor_left.distance_cm()) + "cm")
        print("Right: " + str(sensor_right.distance_cm()) + "cm")
        utime.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
    # test()

