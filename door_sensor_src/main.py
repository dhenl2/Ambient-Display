from hcsr04 import HCSR04
import utime
import math
import gc
from machine import Pin
import uasyncio
from uasyncio import Lock

STD_THRESHOLD = 1  # if accuracy has a spread larger than 1 std then retry
FOUND_TIMEOUT = 2  # (s)
LED = Pin(2, Pin.OUT)
VERBOSE = False

class Time:
    def __init__(self, start_time):
        self.prev_time = 0
        self.curr_time = 0
        self.start_time = start_time

    def get_dt(self):
        self.curr_time = utime.ticks_ms()
        return (self.curr_time - self.prev_time) / 1000

    def get_elapsed(self):
        self.curr_time = utime.ticks_ms()
        return (self.curr_time - self.start_time) / 1000

class Sensor:
    def __init__(self, sensor, name, lock):
        self.sensor = sensor
        self.name = name
        self.lock = lock
        # calibration variables
        self.average = 0
        self.std = 0
        self.error_count = 0
        self.calibration_attempt = 0
        # object detection
        self.found = False
        self.found_time = None
        self.distance = None
        self.start_looking = utime.ticks_ms()

    def reset_found(self):
        if VERBOSE:
            print(self.name + " sensor resetting found")
        self.found = False
        self.found_time = None
        # used to delay looking for someone passing as they pass
        self.start_looking = utime.ticks_ms() + 1000

    def get_found_dt(self):
        curr_time = utime.ticks_ms()
        return (curr_time - self.found_time) / 1000

    def calibrate(self,freq, duration, verbose=False):
        print("Calibrating " + self.name + " at " + str(freq) + "Hz")
        LED.off()
        trials = list()
        time = Time(utime.ticks_ms())
        time.prev_time = time.start_time
        while time.get_elapsed() < duration:
            if time.get_dt() > (1 / freq):
                trials.append(self.sensor.distance_cm())
                time.prev_time = utime.ticks_ms()
        print("Took " + str(time.get_elapsed()) + "s for " + str(len(trials)) +" trials")
        print("Performed at " + str(int(len(trials) / time.get_elapsed())) + "Hz")
        if verbose:
            print(str(trials))
        self.average = int(sum(trials) / len(trials))
        self.std = get_std(trials)
        print("Averaged: " + str(self.average) + " Std: " + str(self.std))
        LED.on()

    async def someone_found(self):
        await self.lock.acquire()
        if self.distance < (self.average - 10) and self.distance != 0:
            self.found = True
            self.found_time = utime.ticks_ms()
            if VERBOSE:
                print("Someone found at " + self.name + " @ " + str(self.found_time) + "ms")
        self.lock.release()

    def get_distance(self, raw=False):
        distance = self.sensor.distance_cm()
        if not raw:
            if (distance > (self.average + (self.std * 3))) or (distance == 0):
                if VERBOSE:
                    print("invalid sensor data for " + self.name)
                    print(str(distance) + " > (" + str(self.average) + " + " + str(self.std * 2) + ") or " + str(
                            distance) + " == 0")
                self.error_count += 1
                # ignore invalid result
                #   - larger than 3 standard deviations of results above the mean which is most likely an error
                #   - or just 0 which is defs an error
                # if error reoccurring attempt to recalibrate
                #   - could be due to an object being placed in the sensors perception
                if self.error_count > 10:
                    self.calibrate(30, 5)
                    self.error_count = 0
                return None

        self.error_count = 0
        return distance

def get_std(trials):
    count = len(trials)
    mean = sum(trials) / count
    variance = 0
    for x in trials:
        variance += abs(x - mean) / count
    std = math.sqrt(variance)
    return std

async def check_for_passers(left_sensor, right_sensor, lock):
    await lock.acquire()
    # check if someone has passed
    if left_sensor.found and right_sensor.found:
        # check which direction they've come
        if left_sensor.found_time < right_sensor.found_time:
            print("Someone came from the left")
        elif left_sensor.found_time > right_sensor.found_time:
            print("Someone came from the right")
        elif left_sensor.found_time == right_sensor.found_time:
            # ignore
            pass
        else:
            print("We've got a wild one boys")
            print(str(right_sensor.found_time) + " ? " + str(left_sensor.found_time))
        left_sensor.reset_found()
        right_sensor.reset_found()
    # check if false reading given or someone attempted to pass in but did not go all the way in
    if left_sensor.found and left_sensor.get_found_dt() > FOUND_TIMEOUT:
        left_sensor.reset_found()
    if right_sensor.found and right_sensor.get_found_dt() > FOUND_TIMEOUT:
        right_sensor.reset_found()
    lock.release()

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

async def thread_get_distance(sensor, frequency):
    time = Time(utime.ticks_ms())
    time.prev_time = utime.ticks_ms()
    while True:
        await uasyncio.sleep_ms(0)
        if time.get_dt() > (1/frequency):
            sensor.distance = sensor.get_distance(raw=True)
            if not sensor.found and (utime.ticks_ms() > sensor.start_looking):
                await sensor.someone_found()
            time.prev_time = utime.ticks_ms()

async def record_log(duration, frequency, sensor_left, sensor_right, lock):
    # record distance
    file = open("record.csv", "w")
    print("Starting Recording Session at " + str(frequency) + "Hz")
    count = 0
    time = Time(utime.ticks_ms())
    time.start_time = utime.ticks_ms()
    time.prev_time = time.start_time
    while time.get_elapsed() < duration:
        await uasyncio.sleep_ms(0)
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

def connect_to_network(ssid, password):
    import network
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(ssid, password)
    if sta_if.isconnected():
        print("Successfully connected to " + ssid)
        return True
    else:
        print("Cannot connect to " + ssid)
        return False

def install_asyncio():
    if connect_to_network("EXETEL E84EE4 2.4G", "HDhuZcsS"):
        import upip
        upip.install('micropython-uasyncio')

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
    loop = uasyncio.get_event_loop()
    loop.create_task(thread_get_distance(sensor_left, frequency))
    loop.create_task(thread_get_distance(sensor_right, frequency))
    loop.run_until_complete(record_log(30, 30, sensor_left, sensor_right, lock))
    print("Leaving main()")
    return

if __name__ == "__main__":
    uasyncio.run(main())
