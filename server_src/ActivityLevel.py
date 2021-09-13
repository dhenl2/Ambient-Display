import os
import numpy as np
import time
import math

directory = "/home/pi/Python/Log/"

class FixedQueue:
    def __init__(self, max_size):
        self.queue = []
        self.max = max_size

    def add(self, value):
        self.queue.append(value)
        if len(self.queue) > self.max:
            self.queue.pop(0)

class ActivityLevel:
    def __init__(self, server):
        self.server = server
        self.people = PeopleCounter()
        self.microphones = FixedQueue(3)
        self.people_levels = {}
        self.people_mean = 8.742316785
        self.people_std = 11.35808511
        self.mic_levels = {}
        self.mic_mean = 59.81290416
        self.mic_std = 3.938022299
        self.calibration_file = open(directory + "activity_calibration.csv", "a")
        self.activity_log_file = open(directory + "activity_levels.csv", "a")
        self.calibrate_again = True
        print(f"Got {len(os.listdir(directory))} log files: {len(os.listdir(directory)) > 2}")
        if len(os.listdir(directory)) > 2:
            self.create_activity_levels()
        else:
            self.set_default_levels()
        # print("Finished constructing ActivityLevels")

    def close_log_files(self):
        self.calibration_file.close()
        self.activity_log_file.close()

    def set_default_levels(self, ):
        print("Setting default levels")
        set_levels(self.mic_levels, self.mic_mean, self.mic_std)
        set_levels(self.people_levels, self.people_mean, self.people_std)
        self.log_calibration_levels(self.mic_levels, "Microphone", self.mic_mean, self.mic_std)
        self.log_calibration_levels(self.people_levels, "People", self.people_mean, self.people_std)

    def log_calibration_levels(self, levels, level_name, mean, std):
        if not time_to_log():
            return
        print("Logging activity levels")
        time_stamp = time.strftime("%d-%m-%Y-%H:%M:%S")
        # log level as time, level 1, level 2, ... , level 6
        record = f"{level_name},{time_stamp},{mean},{std}"
        for key in levels.keys():
            record += ","
            bounds = str(levels.get(key))
            bounds.replace(", ", "-")
            record += bounds
        record += "\n"
        self.calibration_file.write(record)

    def create_activity_levels(self):
        print("Creating activity levels")
        start_time = time.time()
        # get microphone and people data
        mic_files, door_files = get_data_files()
        mic_data = get_data_from_files(mic_files)
        door_data = get_data_from_files(door_files)
        calibrate_mic = calibrate_people = True
        if len(mic_data) == 0:
            print("Setting default for mic levels")
            set_levels(self.mic_levels, self.mic_mean, self.mic_std)
        else:
            print(f"got {len(mic_files)} mic files with {len(mic_data)} data points")
            prev_mic = self.mic_mean, self.mic_std
            self.mic_mean = mic_data.mean()
            self.mic_std = mic_data.std()
            print(f"Mic mean and std {(self.mic_mean, self.mic_std)}")
            set_levels(self.mic_levels, self.mic_mean, self.mic_std)
            self.log_calibration_levels(self.mic_levels, "Microphone", self.mic_mean, self.mic_std)
            # if within_bounds(self.mic_mean, prev_mic[0], 4) and within_bounds(self.mic_std, prev_mic[1], 4):
            #     calibrate_mic = False

        if len(door_data) == 0:
            print("Setting default for door levels")
            set_levels(self.people_levels, self.people_mean, self.people_std)
        else:
            print(f"got {len(door_files)} door files with {len(door_data)} data points")
            prev_people = self.people_mean, self.people_std
            self.people_mean = door_data.mean()
            self.people_std = door_data.std()
            print(f"Door mean and std {(self.people_mean, self.people_std)}")
            # determine levels
            set_levels(self.people_levels, self.people_mean, self.people_std)
            self.log_calibration_levels(self.people_levels, "People", self.people_mean, self.people_std)
            # if within_bounds(self.people_mean, prev_people[0], 3) and within_bounds(self.people_std, prev_people[1], 3):
            #     calibrate_people = False

        if not calibrate_mic and not calibrate_people:
            self.calibrate_again = False
        time_taken = time.time() - start_time
        print(f"Taken {time_taken}s or {time_taken/60}min or {time_taken/ (60 * 60)}hrs")

    def log_level(self, level):
        time_stamp = time.strftime("%d-%m-%Y-%H:%M:%S")
        record = f"{time_stamp},{level}\n"
        self.activity_log_file.write(record)


    def get_level(self):
        people_lvl = get_level_of(self.people.get_count(), self.people_levels)
        print(f"Got people level {people_lvl} with {self.people.get_count()}")
        mic_lvl = get_level_of(self.get_microphone_avg(), self.mic_levels)
        print(f"Got mic level {mic_lvl} with {self.get_microphone_avg()}")
        level = math.floor((people_lvl + mic_lvl) / 2)
        print(f"Got level: {level}")
        self.log_level(level)
        return level

    def get_microphone_avg(self):
        """
        Gets the average of the 2 largest and latest microphone outputs
        """
        least = 100000000
        total = 0
        # sum all items
        for output in self.microphones.queue:
            if output < least:
                least = output
            total += output
        # remove least item to average the two largest
        total -= least
        return total / 2

    def add_mic_input(self, new_input):
        new_input = float(new_input)
        self.microphones.add(new_input)

class Person:
    def __init__(self):
        self.start_time = time.time()
        self.max_time = 3600    # 1hr

    def is_expired(self):
        delta = time.time() - self.start_time
        return delta > self.max_time

class PeopleCounter:
    def __init__(self):
        self.people = []
        self.count = 0

    def add_person(self):
        self.people.append(Person())
        self.count += 1

    def remove_person(self):
        if self.count > 0:
            self.count -= 1
            self.people.pop()

    def get_count(self):
        return self.count

    def check_for_expired(self):
        to_remove = []
        for i in range(len(self.people)):
            person = self.people[i]
            if person.is_expired():
                to_remove.append(i)
        # remove all expired people
        for index in to_remove:
            self.people.pop(index)
        self.count -= len(to_remove)

def within_bounds(value1, value2, bound):
    if (value2 - bound) <= value1 <= (value2 + bound):
        return True
    else:
        return False

def set_levels(levels, mean, std):
    """
    Creates activity levels based on all available data
    Activity levels comprise of 6 levels.
    Level 1 represents data below the 2nd std below the mean
    Level 2 represents data within the 2nd std below the mean
    Level 3 represents data within 1 std of the mean (+/-)
    Level 4 represents data within the 2nd std above the mean
    Level 5 represents data within the 3rd std above the mean
    Level 6 represents data above the 3rd std above the mean
    4 to 6 are ascending levels of excessive activity.
    """
    # set bounds of each level
    levels[1] = (0, max(0, mean - (2 * std)))
    levels[2] = (mean - (2 * std), (mean - std))
    levels[3] = ((mean - std), (mean + std))
    levels[4] = ((mean + std), (mean + (2 * std)))
    levels[5] = ((mean + (2 * std)), (mean + (3 * std)))
    levels[6] = ((mean + (3 * std)), 100000000000000)
    for key in levels.keys():
        print(f"level: {key} is {levels.get(key)}")

def get_level_of(value, level_map):
    for key in level_map.keys():
        bounds = level_map.get(key)
        if bounds[0] <= value <= bounds[1]:
            return key
    return 1

def get_data_from_files(files):
    data = []
    for data_file in files:
        file = open(directory + data_file, "r")
        line = file.readline()
        while line != "":
            # process line
            line_split = line.split(",")
            if len(line_split) > 1:
                value = line_split[1]
                data.append(float(value))
                line = file.readline()
            else:
                # invalid data found
                line = file.readline()
    return np.array(data)

def get_data_files():
    files = os.listdir(directory)
    mic_files = []
    door_files = []
    for file in files:
        if not file == "activity_level.csv":
            file_split = file.split("-")
            if len(file_split) == 1:
                continue
            try:
                if file_split[3] == "microphone.csv":
                    mic_files.append(file)
                elif file_split[3] == "door_sensor.csv":
                    door_files.append(file)
            except IndexError as e:
                print("Got IndexError: " + str(e))
                mic_files = door_files = []
                break
    return mic_files, door_files

def time_to_log():
    days_to_log = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    today = time.strftime("%A")
    now_time = int(time.strftime("%H"))
    if today in days_to_log and 8 <= now_time <= 14:
        return True
    else:
        return False