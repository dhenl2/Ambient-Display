import utime
import math
from machine import Pin
import uasyncio

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

async def check_for_passers(left_sensor, right_sensor, lock, server=False):
    await lock.acquire()
    result = None
    # check if someone has passed
    if left_sensor.found and right_sensor.found:
        # check which direction they've come
        if left_sensor.found_time < right_sensor.found_time:
            if server:
                result = -1
            print("Someone came from the left")
        elif left_sensor.found_time > right_sensor.found_time:
            if server:
                result = 1
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
    return result

async def thread_get_distance(sensor, frequency):
    time = Time(utime.ticks_ms())
    time.prev_time = utime.ticks_ms()
    while True:
        await uasyncio.sleep_ms(0)
        if time.get_dt() > (1 / frequency):
            sensor.distance = sensor.get_distance(raw=True)
            if not sensor.found and (utime.ticks_ms() > sensor.start_looking):
                await sensor.someone_found()
            time.prev_time = utime.ticks_ms()