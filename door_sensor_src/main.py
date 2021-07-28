from door_sensor import Time, Sensor, check_for_passers, thread_get_distance
import uasyncio as asyncio
from uasyncio import Lock
import gc
from hcsr04 import HCSR04
import utime
import usocket as socket

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

    async def run_program(sock):
        print("Starting running program")
        while True:
            sock_writer = asyncio.StreamWriter(sock, {})
            while True:
                try:
                    result = await check_for_passers(sensor_left, sensor_right, lock, True)
                    if result is not None:
                        result = str(result) + '\0'
                        result = bytes(str(result), 'utf-8')
                        await sock_writer.awrite(result)
                except OSError:
                    close(sock)
                await asyncio.sleep_ms(0)

    while True:
        conn = await connect()
        await run_program(conn)

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

if __name__ == "__main__":
    asyncio.run(main())
