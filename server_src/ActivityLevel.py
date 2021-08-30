import os
import numpy as np
import time
import math

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
        self.people_mean = 0
        self.people_std = 0
        self.mic_levels = {}
        if len(os.listdir("Log/")) > 0:
            self.create_activity_levels()
        else:
            self.set_default_levels()
        self.mic_mean = 0
        self.mic_std = 0
        self.log_file = open("Log/activity_level.csv" , "a")
        self.calibrate_again = True

    def set_default_levels(self):
        # preset levels so it only operates on level 1 till optimised
        self.people_levels = {
            1: (0, 10000),
            2: (10000, 10001),
            3: (10001, 10002),
            4: (10002, 10003),
            5: (10003, 10004),
            6: (10004, 10005)
        }
        self.mic_levels = {
            1: (0, 10000),
            2: (10000, 10001),
            3: (10001, 10002),
            4: (10002, 10003),
            5: (10003, 10004),
            6: (10004, 10005)
        }
    
    def log_activity_levels(self, levels, level_name):
        day = time.localtime().tm_mday
        month = time.localtime().tm_mon
        year = time.localtime().tm_year
        hour = time.localtime().tm_hour
        minutes = time.localtime().tm_min
        seconds = time.localtime().tm_sec
        time_stamp = f"{day}-{month}-{year}-{hour}:{minutes}:{seconds}"
        # log level as time, level 1, level 2, ... , level 6
        record = level_name + "," + time_stamp
        for key in levels.keys():
            record += ","
            bounds = str(levels.get(key))
            bounds.replace(", ", "-")
            record += bounds
        record += "\n"
        self.log_file.write(record)

    def create_activity_levels(self, ):
        # get microphone and people data
        mic_files, door_files = get_data_files()
        mic_data = get_data_from_files(mic_files)
        door_data = get_data_from_files(door_files)
        # record prev mean and std and save current mean and std
        prev_mic = self.mic_mean, self.mic_std
        prev_people = self.people_mean, self.people_std
        self.mic_mean = mic_data.mean()
        self.mic_std = mic_data.std()
        self.people_mean = door_data.mean()
        self.people_std = door_data.std()
        # determine levels
        set_levels(self.mic_levels, self.mic_mean, self.mic_std)
        set_levels(self.people_levels, self.people_mean, self.people_std)
        self.log_activity_levels(self.mic_levels, "Microphone")
        self.log_activity_levels(self.people_levels, "People")
        # check if calibration is the same as before
        if (within_bounds(self.mic_mean, prev_mic[0], 4) and within_bounds(self.mic_std, prev_mic[1], 4)) or \
                (within_bounds(self.people_mean, prev_people[0], 3) and within_bounds(self.people_std, prev_people[1], 3)):
            self.calibrate_again = False

    def get_level(self):
        people_lvl = get_level_of(self.people.get_count(), self.people_levels)
        mic_lvl = get_level_of(self.get_microphone_avg(), self.mic_levels)
        return math.floor((people_lvl + mic_lvl) / 2)

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

def get_level_of(value, level_map):
    for key in level_map.keys():
        bounds = level_map.get(key)
        if bounds[0] <= value <= bounds[1]:
            return value
    return 1

def get_data_from_files(files):
    data = []
    for data_file in files:
        file = open("Log/" + data_file, "r")
        line = file.readline()
        while line != "":
            # process line
            line_split = line.split(",")
            if len(line_split) > 1:
                value = line_split[1]
                data.append(float(value))
            else:
                # invalid data found
                continue
    return np.array(data)

def get_data_files():
    files = os.listdir("Log/")
    mic_files = []
    door_files = []
    for file in files:
        file_split = file.split("-")
        if file_split[3] == "microphone.csv":
            mic_files.append(file)
        elif file_split[3] == "door_sensor.csv":
            door_files.append(file)
    return mic_files, door_files