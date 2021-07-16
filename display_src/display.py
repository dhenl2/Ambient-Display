import neopixel
from machine import Pin
import time
import utime
import uasyncio

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
    def __init__(self, items, restrict=False):
        self.items = items
        self.index = 0
        self.restrict = restrict
        self.start = True

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

    def get_current(self):
        return self.items[self.index]

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


class LoopSequence:
    def __init__(self, pixels, colours, rate=1):
        self.pixels = Queue(pixels)
        self.colours = Queue(colours)
        self.rate = rate
        self.time = Time()

    def set_color_rate(self, colours, rate):
        self.colours = Queue(colours)
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


def animation_idea_1(pin, user: UserInput):
    np = neopixel.NeoPixel(pin, 24)

    str_colours = ("Dark Blue", "Blue", "Light Blue", "Dark Green", "Green", "Light Green", "Yellow", "Orange", "Red")
    colours = (DARK_BLUE, BLUE, LIGHT_BLUE, DARK_GREEN, GREEN, LIGHT_GREEN, YELLOW, ORANGE, RED)
    colours = list(zip(colours, create_blank_list(len(colours))))
    rate_list = create_rate_list(1, 0.05, len(colours))
    colour_rate_list = list(zip(colours, str_colours, rate_list))
    colour_rate_list = Queue(colour_rate_list)
    n_colour, str_colour, n_rate = colour_rate_list.get_next()
    print("Starting colour %s rate %f" % (str_colour, n_rate))
    start_colour_rate = (GREY, BLANK), 1

    top = LoopSequence(line_1, start_colour_rate[0], rate=start_colour_rate[1])
    mid = LoopSequence(line_2, start_colour_rate[0], rate=start_colour_rate[1])
    bot = LoopSequence(line_3, start_colour_rate[0], rate=start_colour_rate[1])

    while True:
        # check for user input
        user_read = user.read_input()
        if user_read == "inc" or user_read == "dec":
            if user_read == "inc":
                n_colour, str_colour, n_rate = colour_rate_list.get_next()
                bot.set_color_rate(n_colour, n_rate)
                # TODO start to cycle next colour from bottom -> top
            else:
                n_colour, str_colour, n_rate - colour_rate_list.get_prev()
                top.set_color_rate(n_colour, n_rate)
                # TODO start to cycle next colour from top -> bottom

        # cycle top
        if top.time_to_cycle():
            turn_on(np, top.pixels.get_next(), top.colours.get_next())
        # cycle middle
        if mid.time_to_cycle():
            turn_on(np, mid.pixels.get_next(), mid.colours.get_next())
        # cycle bottom
        if bot.time_to_cycle():
            turn_on(np, bot.pixels.get_next(), bot.colours.get_next())

        if disp_bot.cycled:
            if not disp_bot.wait:
                print("Adding colour %s to bottom" % str_colour)
                disp_bot.add_colours((n_colour, BLANK))
                disp_bot.wait = True
                disp_mid.cycled = False
            if disp_mid.cycled:
                if not disp_mid.wait:
                    print("Adding colour %s to middle" % str_colour)
                    disp_mid.add_colours((n_colour, BLANK))
                    disp_mid.wait = True
                    disp_top.cycled = False
                if disp_top.cycled:
                    if not disp_top.wait:
                        print("Adding colour %s to top" % str_colour)
                        disp_top.add_colours((n_colour, BLANK))
                        disp_top.wait = True
                    else:
                        # read end of cycle for colour going from bottom to top
                        # start new colour and rate
                        n_colour, str_colour, n_rate = colour_rate_list.get_next()
                        disp_top.cycled = disp_mid.cycled = False
                        disp_top.wait = disp_mid.wait = disp_bot.wait = False
                        print("Starting colour %s" % str_colour)



def run_line_animation(pin, rate):
    np = neopixel.NeoPixel(pin, 24)
    loop_1 = LoopSequence(line_1, (DARK_BLUE, BLANK, BLUE, BLANK, LIGHT_BLUE, BLANK))
    loop_2 = LoopSequence(line_2, (DARK_GREEN, BLANK, GREEN, BLANK, LIGHT_GREEN, BLANK))
    loop_3 = LoopSequence(line_3, (RED, BLANK, ORANGE, BLANK, YELLOW, BLANK))
    colour_1 = loop_1.get_next_colour()
    colour_2 = loop_2.get_next_colour()
    colour_3 = loop_3.get_next_colour()

    while 1:
        turn_on(np, loop_1.get_next_pixels(), colour_1)
        turn_on(np, loop_2.get_next_pixels(), colour_2)
        turn_on(np, loop_3.get_next_pixels(), colour_3)
        time.sleep(rate)
        if loop_1.last_pixels():
            colour_1 = loop_1.get_next_colour()
        if loop_2.last_pixels():
            colour_2 = loop_2.get_next_colour()
        if loop_3.last_pixels():
            colour_3 = loop_3.get_next_colour()


def run_circle(pin):
    np = neopixel.NeoPixel(pin, 24)
    stages = (circle_1, circle_2, circle_3)
    colours = (RED, GREEN, BLUE)
    for index in range(3):
        # set lights to red
        turn_on(np, stages[index], colours[index])
        time.sleep(3)
        turn_off(np, stages[index])

