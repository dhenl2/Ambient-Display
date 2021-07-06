from hcsr04 import HCSR04
import utime
import math
import gc

STD_THRESHOLD = 1  # if accuracy has a spread larger than 1 std then retry
FOUND_TIMEOUT = 2  # (s)

def get_std(trials):
    count = len(trials)
    mean = sum(trials) / count
    variance = 0
    for x in trials:
        variance += abs(x - mean) / count
    std = math.sqrt(variance)
    return std

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
    def __init__(self, sensor, name):
        self.name = name
        self.sensor = sensor
        self.average = 0
        self.std = 0
        self.found = False
        self.found_time = None
        self.error_count = 0
        # self.calibration_attempt = 0

    def reset_found(self):
        print("Resetting found")
        self.found = False
        self.found_time = None

    def get_found_dt(self):
        curr_time = utime.ticks_ms()
        return (curr_time - self.found_time) / 1000

    def calibrate(self, freq, verbose=False):
        print("Calibrating " + self.name + " at " + str(freq) + "Hz")
        trials = list()
        time = Time(utime.ticks_ms())
        time.prev_time = time.start_time
        while time.get_elapsed() < 10:
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
        # if self.calibration_attempt < 5 and self.std > STD_THRESHOLD:
        #     print("Attempt to recalibrate")
        #     self.calibration_attempt += 1
        #     self.calibrate()

    def someone_found(self, distance):
        # if distance < (self.calibrated - self.std):
        if distance < (self.average - 10) and distance != 0:
            print("someone found with " + str(distance) + " < (" + str(self.average) + " - 10)")
            self.found = True
            self.found_time = utime.ticks_ms()

    def get_distance(self, raw=False):
        distance = self.sensor.distance_cm()
        if not raw:
            if (distance > (self.average + (self.std * 2))) or (distance == 0):
                print("invalid sensor data for " + self.name)
                print(str(distance) + " > (" + str(self.average) + " + " + str(self.std * 2) + ") or " + str(
                    distance) + " == 0")
                self.error_count += 1
                # ignore invalid result
                #   - larger than 68% of results above the mean which is most likely an error
                #   - or just 0 which is defs an error
                # if error reoccurring attempt to recalibrate
                # if self.error_count > 5:
                #     self.calibrate(True)
                #     self.error_count = 0
                # return None
        self.error_count = 0
        return distance

def check_for_passers(left_sensor, right_sensor):
    # check if someone has passed
    if left_sensor.found and right_sensor.found:
        # check which direction they've come
        if left_sensor.found_time < right_sensor.found_time:
            print("Someone came in")
        elif right_sensor.found_time > left_sensor.found_time:
            print("Someone left")
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
    left_distance = left_sensor.get_distance()
    right_distance = right_sensor.get_distance()

    check_for_passers(left_sensor, right_sensor)

    # Check if distance is invalid or check if someone is passing
    if left_distance is None:
        left_distance = ""
    else:
        left_distance = int(left_distance)
        left_sensor.someone_found(left_distance)

    if right_distance is None:
        right_distance = ""
    else:
        right_distance = int(right_distance)
        right_sensor.someone_found(right_distance)

    data = str(time.get_elapsed()) + "," + str(left_sensor.average) + "," + str(left_distance) + "," + \
           str(right_sensor.average) + "," + str(right_distance) + "\n"
    if header:
        file.write("time (s),Left (avg),Left,Right (avg),Right\n")
    file.write(data)

def main():
    garbage = gc
    frequency = 30 # hz
    sensor_left = Sensor(HCSR04(trigger_pin=14, echo_pin=12), "left")
    sensor_right = Sensor(HCSR04(trigger_pin=5, echo_pin=4), "right")
    sensor_left.calibrate(frequency)
    sensor_right.calibrate(frequency)
    garbage.collect()
    garbage.enable()

    # record distance
    file = open("record.csv", "w")
    print("Starting Recording Session at " + str(frequency) + "Hz")
    count = 0
    time = Time(utime.ticks_ms())
    time.start_time = utime.ticks_ms()
    time.prev_time = time.start_time
    while count < 1000:
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

if __name__ == "__main__":
    main()
