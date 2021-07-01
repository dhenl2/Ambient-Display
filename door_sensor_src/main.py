from hcsr04 import HCSR04
import time

if __name__ == "__main__":
    sensor_right = HCSR04(trigger_pin=5, echo_pin=4)
    sensor_left = HCSR04(trigger_pin=14, echo_pin=12)
    while True:
        print("Distance_left: " + str(int(sensor_left.distance_cm())) + "cm\n" +
              "Distance_right: " + str(int(sensor_right.distance_cm())) + "cm")
        time.sleep(1)