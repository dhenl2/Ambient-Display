from hcsr04 import HCSR04
import time
import math


def get_variance(trials):
    count = len(trials)
    mean = sum(trials) / count
    variance = 0
    for x in trials:
        variance += abs(x - mean) / count
    print("Variance: " + str(variance))
    std = math.sqrt(variance)
    print("Standard Deviation: " + str(std))
    return variance, std


class Sensor:
    def __init__(self, sensor):
        self.sensor = sensor
        self.calibrated = 0
        self.variance = 0
        self.std = 0
        self.found = None

    def calibrate(self):
        trials = list()
        time_start = time.time()
        for i in range(1000):
            trials.append(self.sensor.distance_cm())
        time_end = time.time()
        print("Took " + str(time_end - time_start) + "s for 1000 trials")
        self.calibrated = int(sum(trials) / len(trials))
        self.variance, self.std = get_variance(trials)
        print("Calibrated: " + str(self.calibrated))

    def someone_found(self, distance):
        # if distance < (self.calibrated - self.std):
        if distance < (self.calibrated - 10) and distance != 0:
            print("someone found with " + str(distance) + " < (" + str(self.calibrated) + " - 10)")
            self.found = time.time()

    def get_distance(self):
        distance = self.sensor.distance_cm()
        if (distance > (self.calibrated + self.std)) or (distance == 0):
            # ignore invalid result
            #   - larger than 68% of results above the mean which is most likely an error
            #   - or just 0 which is defs an error
            return None
        return self.sensor.distance_cm()


def write_data(file, left_sensor, right_sensor):
    left_distance = left_sensor.get_distance()
    right_distance = right_sensor.get_distance()

    # check if someone has passed
    if left_sensor.found is not None and right_sensor.found is not None:
        # check which direction they've come
        if left_sensor.found < right_sensor.found:
            print("Someone came in")
        elif right_sensor.found > left_sensor.found:
            print("Someone left")
        else:
            print("We've got a wild one boys")
        left_sensor.found = None
        right_sensor.found = None

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

    data = str(left_sensor.calibrated) + "," + str(left_distance) + "," + \
           str(right_sensor.calibrated) + "," + str(right_distance) + "\n"
    file.write(data)


def main():
    sensor_right = Sensor(HCSR04(trigger_pin=5, echo_pin=4))
    sensor_left = Sensor(HCSR04(trigger_pin=14, echo_pin=12))
    print("Left")
    sensor_left.calibrate()
    print("Right")
    sensor_right.calibrate()
    # while True:
    #     print("Left: " + str(int(sensor_left.get_distance())) + "cm\nRight: " + str(int(sensor_right.get_distance())) + "cm")
    #     time.sleep(0.4)

    # record distance
    file = open("record.csv", "w")
    print("Starting Recording Session")
    file.write("Left,Left (avg),Right,Right (avg)\n")

    count = 0
    while count < 500:
        write_data(file, sensor_left, sensor_right)
        count += 1
    file.close()
    print("Ending Recording Session")


if __name__ == "__main__":
    main()
