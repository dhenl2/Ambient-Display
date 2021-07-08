from hcsr04 import HCSR04
import utime
import math
import gc
from machine import Pin
import uasyncio

STD_THRESHOLD = 1  # if accuracy has a spread larger than 1 std then retry
FOUND_TIMEOUT = 2  # (s)
LED = Pin(2, Pin.OUT)
VERBOSE = True

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
    def __init__(self, queue, sensor, name):
        self.queue = queue
        self.sensor = sensor
        self.name = name
        self.average = 0
        self.std = 0
        self.found = False
        self.found_time = None
        self.error_count = 0
        self.calibration_attempt = 0
        self.distance = None


    def reset_found(self):
        if VERBOSE:
            print("Resetting found")
        self.found = False
        self.found_time = None

    def get_found_dt(self):
        curr_time = utime.ticks_ms()
        return (curr_time - self.found_time) / 1000

    async def calibrate(self,freq, duration, verbose=False):
        print("Calibrating " + self.name + " at " + str(freq) + "Hz")
        LED.off()
        trials = list()
        time = Time(utime.ticks_ms())
        time.prev_time = time.start_time
        while time.get_elapsed() < duration:
            if time.get_dt() > (1 / freq):
                trials.append(self.sensor.distance_cm())
                time.prev_time = utime.ticks_ms()
        print("Took " + str(time.get_elapsed()) + "s for 1000 trials")
        print("Performed at " + str(int(len(trials) / time.get_elapsed())) + "Hz")
        if verbose:
            print(str(trials))
        self.average = int(sum(trials) / len(trials))
        self.std = get_std(trials)
        print("Averaged: " + str(self.average) + " Std: " + str(self.std))
        LED.on()
        self.queue.task_done()

    def someone_found(self):
        # if distance < (self.calibrated - self.std):
        if self.distance < (self.average - 10) and self.distance != 0:
            if VERBOSE:
                print("Someone found at " + self.name + " @ " + str(self.found_time) + "ms")
            self.found = True
            self.found_time = utime.ticks_ms()


    async def get_distance(self, raw=False):
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
                if self.error_count > 10:
                    await self.calibrate(30, 5)
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

def check_for_passers(left_sensor, right_sensor):
    # check if someone has passed
    if left_sensor.found and right_sensor.found:
        # check which direction they've come
        if left_sensor.found_time < right_sensor.found_time:
            print("Someone came from the left")
        elif right_sensor.found_time > left_sensor.found_time:
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


def write_data(file, left_sensor, right_sensor, time, header=False):
    check_for_passers(left_sensor, right_sensor)
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


async def thread_get_distance(sensor):
    while True:
        sensor.distance = await sensor.get_distance()
        sensor.someone_found()

async def record_log(duration, frequency, sensor_left, sensor_right):
    # record distance
    file = open("record.csv", "w")
    print("Starting Recording Session at " + str(frequency) + "Hz")
    count = 0
    time = Time(utime.ticks_ms())
    time.start_time = utime.ticks_ms()
    time.prev_time = time.start_time
    while time.get_elapsed() < duration:
        if time.get_dt() > (1 / frequency):
            # show progress
            if count != 0 and count % 100 == 0:
                percentage = float(count) / 10
                percentage = str(percentage)
                print("{0}% @ {1}s".format(str(percentage), time.get_elapsed()))
                # print(percentage + "% @ " + time.get_elapsed() + "s")

            if count == 0:
                write_data(file, sensor_left, sensor_right, time, True)
            else:
                write_data(file, sensor_left, sensor_right, time)
            time.prev_time = utime.ticks_ms()
            count += 1
    file.close()
    print("Ending Recording Session")
    return

def main():
    garbage = gc
    frequency = 30 # hz
    q = uasyncio.Queue()
    sensor_left = Sensor(q, HCSR04(trigger_pin=14, echo_pin=12), "left")
    sensor_right = Sensor(q, HCSR04(trigger_pin=5, echo_pin=4), "right")
    cal_left = uasyncio.create_task(sensor_left.calibrate(frequency, 10))
    cal_right = uasyncio.create_task(sensor_right.calibrate(frequency, 10))
    await uasyncio.gather([cal_left, cal_right])
    await q.join()
    garbage.collect()
    garbage.enable()

    # threads
    left = uasyncio.create_task(thread_get_distance(sensor_left))
    right = uasyncio.create_task(thread_get_distance(sensor_right))
    record = uasyncio.create_task(record_log(30, 30, sensor_left, sensor_right))
    await uasyncio.gather([left, right, record])
    uasyncio.wait_for(record)
    print("Leaving Main()")
    return


if __name__ == "__main__":
    main()
