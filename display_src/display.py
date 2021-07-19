import neopixel
from machine import Pin
import time
import utime
import uasyncio as asyncio

# Colours
from main import UserInput

RED = (255, 0, 0)
ORANGE = (255, 128, 0)
YELLOW = (255, 255, 0)
DARK_GREEN = (0, 102, 0)
GREEN = (0, 204, 0)
LIGHT_GREEN = (102, 255, 102)
DARK_BLUE = (0, 0, 102)
BLUE = (0, 0, 255)
LIGHT_BLUE = (102, 178, 255)
BLANK = (0, 0, 0)
GREY = (96, 96, 96)

# layers
circle_1 = [9, 13, 14, 19]
circle_2 = [1, 3, 4, 8, 10, 12, 15, 18, 20, 22]
circle_3 = [0, 2, 5, 6, 7, 11, 16, 17, 21]

# Horizontal Lines
line_1 = [[None], [22], [23, 19], [18], [17, 15], [16], [None]]
line_2 = [[21], [20, 12], [13], [14, 9], [8], [7, 5], [6]]
line_3 = [[None], [11], [10, 2], [3], [4, 1], [0], [None]]

class Time:
    def __init__(self):
        self.prev_time = 0
        self.curr_time = 0
        self.start_time = utime.ticks_ms()

    def get_dt(self):
        self.curr_time = utime.ticks_ms()
        return (self.curr_time - self.prev_time) / 1000

    def get_elapsed(self):
        self.curr_time = utime.ticks_ms()
        return (self.curr_time - self.start_time) / 1000

    def start_timer(self):
        self.prev_time = utime.ticks_ms()


class Queue:
    def __init__(self, items, name, restrict=False):
        if items is None:
            self.items = list()
        else:
            self.items = items
        self.index = 0
        self.restrict = restrict
        self.start = True
        self.name = name

    def get_next(self):
        if self.start:
            self.start = False
            return self.items[0]

        self.index += 1
        if self.index == len(self.items):
            if self.restrict:
                self.index -= 1
            else:
                self.index = 0
        return self.items[self.index]

    def get_prev(self):
        if self.start:
            self.start = False
            return self.items[0]

        self.index -= 1
        if self.index == -1:
            if self.restrict:
                self.index = 0
            else:
                self.index = len(self.items) - 1
        return self.items[self.index]

    def get_after_next(self):
        return self.items[self.index + 1]

    def get_current(self):
        return self.items[self.index]

    def get_first(self):
        return self.items[0]

    def at_start_index(self):
        if self.index == 0:
            return True
        else:
            return False

    def at_last_index(self):
        if self.index == (len(self.items) - 1):
            return True
        else:
            return False

    def add_item(self, item):
        self.items.append(item)
        print("\titems in %s is now %s" % (self.name, self.items))

    def pop(self):
        # print("popping item from " + self.name)
        # print("currently have %d in items list: %s" % (self.get_size(), str(self.items)))
        popped = self.items.pop(0)
        # print("popped item " + str(popped))
        # print("items in list " + str(self.items))

    def get_size(self):
        return len(self.items)

    def restart(self):
        self.index = 0
        self.start = True


class LoopSequence:
    def __init__(self, pixels, colours, name, rate=1):
        self.pixels = Queue(pixels, "pixels")
        self.colours = Queue(colours, "colours")
        self.name = name
        self.rate = rate
        self.time = Time()

    def set_color_rate(self, colours, rate):
        self.colours = Queue(colours, "colours")
        self.rate = rate

    def completed_cycle(self):
        if self.pixels.at_last_index() and self.colours.at_last_index():
            return True
        else:
            return False

    def time_to_cycle(self):
        if self.time.get_dt() > self.rate:
            self.time.prev_time = utime.ticks_ms()
            return True
        else:
            return False

def turn_on(np, stage, colour):
    for pixel in stage:
        if pixel is None:
            continue
        np[pixel] = colour
    np.write()


def turn_off(np, stage):
    for pixel in stage:
        np[pixel] = (0, 0, 0)
    np.write()


def run_sequence(pin):
    np = neopixel.NeoPixel(pin, 24)
    for pixel in range(24):
        np[pixel] = RED
        np.write()
        time.sleep(2)
        np[pixel] = BLANK
        np.write()


def create_rate_list(start, end, num):
    rate_list = list()
    decrement = (start - end) / num
    for i in range(num):
        rate_list.append(start)
        start -= decrement
    return rate_list

def create_blank_list(num):
    blanks = list()
    for i in range(num):
        blanks.append(BLANK)
    return blanks

def do_row_cycle(main_queue, queue):
    colour_rate, row_queue = queue
    if row_queue.get_current().completed_cycle():
        print("row %s completed a cycle" % row_queue.get_current().name)
        if row_queue.at_last_index():
            # cycled colour through all rows, time to remove
            print("\trow colour cycled through ")
            main_queue.pop()
            # row_queue.restart()
        else:
            # pass colour onto next row
            row = row_queue.get_next()
            colour, rate = colour_rate
            print("\tSetting colour %s to row %s" % (colour, row.name))
            row.set_color_rate(colour, rate)

def check_colour_pass(queue):
    # check if there are items in the colour queue to cycle thru
    if queue.get_size() != 0:
        do_row_cycle(queue, queue.get_current())
        if queue.get_size() > 1:
            # start next in line
            do_row_cycle(queue, queue.get_after_next())

def cycle_rows(rows, np):
    for row in rows:
        if row.time_to_cycle():
            if row.pixels.at_last_index():
                turn_on(np, row.pixels.get_next(), row.colours.get_next())
            else:
                turn_on(np, row.pixels.get_next(), row.colours.get_current())


def animation_idea_1(pin, user: UserInput):
    np = neopixel.NeoPixel(pin, 24)

    str_colours = ("Blue", "Light Blue", "Green", "Yellow", "Orange", "Red")
    colours = (BLUE, LIGHT_BLUE, GREEN, YELLOW, ORANGE, RED)
    colours = list(zip(colours, create_blank_list(len(colours))))
    rate_list = create_rate_list(1, 0.05, len(colours))
    colour_rate_list = list(zip(colours, str_colours, rate_list))
    colour_rate_list = Queue(colour_rate_list, "colour_rate", restrict=True)
    start_colour_rate = (GREY, BLANK), 1

    top = LoopSequence(line_1, start_colour_rate[0], "top", rate=start_colour_rate[1])
    mid = LoopSequence(line_2, start_colour_rate[0], "middle", rate=start_colour_rate[1])
    bot = LoopSequence(line_3, start_colour_rate[0], "bottom", rate=start_colour_rate[1])

    command_queue = Queue(None, "commands")

    while True:
        # check for user input
        await asyncio.sleep_ms(0)
        user_read = await user.read_input()

        if user_read is not None:
            if user_read == "inc":
                n_colour, str_colour, n_rate = colour_rate_list.get_next()
                print("Adding colour %s to queue" % str_colour)
                command_queue.add_item(((n_colour, n_rate), Queue((bot, mid, top), "inc_row")))
            else:
                n_colour, str_colour, n_rate = colour_rate_list.get_prev()
                print("Adding colour %s to queue" % str_colour)
                command_queue.add_item(((n_colour, n_rate), Queue((top, mid, bot), "dec_row")))
            if command_queue.get_size() == 1:
                # start queue
                start_colour_rate, start_rows = command_queue.get_first()
                start_colour, start_rate = start_colour_rate
                start_row = start_rows.get_first()
                command_queue.start = False
                start_row.set_color_rate(start_colour, start_rate)
            await user.reset_input()

        check_colour_pass(command_queue)
        cycle_rows((top, mid, bot), np)

# def run_line_animation(pin, rate):
#     np = neopixel.NeoPixel(pin, 24)
#     loop_1 = LoopSequence(line_1, (DARK_BLUE, BLANK, BLUE, BLANK, LIGHT_BLUE, BLANK))
#     loop_2 = LoopSequence(line_2, (DARK_GREEN, BLANK, GREEN, BLANK, LIGHT_GREEN, BLANK))
#     loop_3 = LoopSequence(line_3, (RED, BLANK, ORANGE, BLANK, YELLOW, BLANK))
#     colour_1 = loop_1.get_next_colour()
#     colour_2 = loop_2.get_next_colour()
#     colour_3 = loop_3.get_next_colour()
#
#     while 1:
#         turn_on(np, loop_1.get_next_pixels(), colour_1)
#         turn_on(np, loop_2.get_next_pixels(), colour_2)
#         turn_on(np, loop_3.get_next_pixels(), colour_3)
#         time.sleep(rate)
#         if loop_1.last_pixels():
#             colour_1 = loop_1.get_next_colour()
#         if loop_2.last_pixels():
#             colour_2 = loop_2.get_next_colour()
#         if loop_3.last_pixels():
#             colour_3 = loop_3.get_next_colour()


def run_circle(pin):
    np = neopixel.NeoPixel(pin, 24)
    stages = (circle_1, circle_2, circle_3)
    colours = (RED, GREEN, BLUE)
    for index in range(3):
        # set lights to red
        turn_on(np, stages[index], colours[index])
        time.sleep(3)
        turn_off(np, stages[index])

