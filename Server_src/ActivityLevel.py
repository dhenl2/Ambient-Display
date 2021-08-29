import numpy as np
from queue import Queue
import time

class ActivityLevel:
    def __init__(self, server):
        self.server = server
        self.people = PeopleCounter()
        self.microphones = Queue()
        self.microphones.maxsize = 3
        # preset levels so it only operates on level 1 till optimised
        self.levels = {
            1: (0, 10000),
            2: (10000, 10001),
            3: (10001, 10002),
            4: (10002, 10003),
            5: (10003, 10004),
            6: (10004, 10005)
        }
        self.log_file = open("activity_level.csv" , "a")
    
    def log_activity_levels(self):
        day = time.localtime().tm_mday
        month = time.localtime().tm_mon
        year = time.localtime().tm_year
        hour = time.localtime().tm_hour
        minutes = time.localtime().tm_min
        seconds = time.localtime().tm_sec
        time_stamp = f"{day}-{month}-{year}-{hour}:{minutes}:{seconds}"
        # log level as time, level 1, level 2, ... , level 6
        record = time_stamp
        for key in self.levels.keys():
            record += ","
            bounds = str(self.levels.get(key))
            bounds.replace(", ", "-")
            record += bounds

    def create_activity_levels(self):
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
        mic_files, door_files = get_data_files()
        mic_data = get_data_from_files(mic_files)
        door_data = get_data_from_files(door_files)
        mean = mic_data.mean() + door_data.mean()
        variance = mic_data.var() + door_data.var() + (2 * np.cov(mic_data, door_data)[0][1])
        std = np.sqrt(variance)
        # set bounds of each level
        self.levels[1] = (0, mean - (2 * std))
        self.levels[2] = (mean - (2 * std), (mean - std))
        self.levels[3] = ((mean - std), (mean + std))
        self.levels[4] = ((mean + std), (mean + (2 * std)))
        self.levels[5] = ((mean + (2 * std)), (mean + (3 * std)))
        self.levels[6] = ((mean + (3 * std)), 100000000000000)

        self.log_activity_levels()

    def get_level(self):
        value = self.get_output()
        for key in self.levels.keys():
            bounds = self.levels.get(key)
            if bounds[0] <= value <= bounds[1]:
                return value
        return 1

    def get_output(self):
        return self.people.get_count() + self.get_microphone_avg()

    def get_microphone_avg(self):
        """
        Gets the average of the 2 largest and latest microphone outputs
        """
        least = 100000000
        total = 0
        # sum all items
        for output in list(self.microphones.queue):
            if output < least:
                least = output
            total += output
        # remove least item to average the two largest
        total -= least
        return total / 2

    def add_mic_input(self, new_input):
        new_input = float(new_input)
        self.microphones.put(new_input)

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

def get_data_from_files(files):
    data = []
    for data_file in files:
        file = open(data_file, "r")
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