import neopixel
from machine import Pin
import time
import utime
import uasyncio

# idea
# - shift colour indicator from bottom to top

# Colours
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

# layers
circle_1 = [9, 13, 14, 19]
circle_2 = [1, 3, 4, 8, 10, 12, 15, 18, 20, 22]
circle_3 = [0, 2, 5, 6, 7, 11, 16, 17, 21]

# Animated Lines
line_1 = [[None], [22], [23, 19], [18], [17, 15], [16], [None]]
line_2 = [[21], [20, 12], [13], [14, 9], [8], [7, 5], [6]]
line_3 = [[None], [11], [10, 2], [3], [4, 1], [0], [None]]

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

    def start_index(self):
        if self.index == 0:
            return True
        else:
            return False


class LoopSequence:
    def __init__(self, pixels, colours):
        self.pixels = pixels
        self.colours = colours
        self.colour_index = 0
        self.pixel_index = 0
        self.first_pixel = True
        self.first_colour = True
        self.changed = False
        self.cycled = False
        self.wait = False

    def add_colours(self, colours):
        self.colours = colours
        self.colour_index = 0
        self.cycled = False

    def get_next_pixels(self):
        if self.last_colour() and self.last_pixels():
            self.cycled = True

        if self.first_pixel:
            self.first_pixel = False
        else:
            self.pixel_index += 1
            if self.pixel_index == len(self.pixels):
                self.pixel_index = 0

        return self.pixels[self.pixel_index]

    def get_next_colour(self):
        if self.first_colour:
            self.first_colour = False
        else:
            if self.last_pixels():
                self.colour_index += 1
                if self.colour_index == len(self.colours):
                    self.colour_index = 0

        return self.colours[self.colour_index]

    def get_prev_pixels(self):
        pixel_index = colour_index = 0
        if self.pixel_index == 0:
            pixel_index = len(self.pixels) - 1
        else:
            pixel_index = self.pixel_index - 1

        return self.pixels[pixel_index]

    def get_prev_colour(self):
        if self.colour_index == 0:
            colour_index = len(self.colours) - 1
        else:
            colour_index = self.colour_index - 1

        return self.colours[colour_index]

    def last_colour(self):
        return self.colour_index == len(self.colours) - 1

    def last_pixels(self):
        return self.pixel_index == len(self.pixels) - 1


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


def animation_idea_1(pin):
    np = neopixel.NeoPixel(pin, 24)
    str_colours = ("Dark Blue", "Blue", "Light Blue", "Dark Green", "Green", "Light Green", "Yellow", "Orange", "Red")
    colours = (DARK_BLUE, BLUE, LIGHT_BLUE, DARK_GREEN, GREEN, LIGHT_GREEN, YELLOW, ORANGE, RED)
    rate_list = create_rate_list(1, 0.05, len(colours))
    colour_rate_list = list(zip(colours, str_colours, rate_list))
    colour_rate_list = Queue(colour_rate_list)
    n_colour, str_colour, n_rate = colour_rate_list.get_next()
    print("Starting colour %s rate %f" % (str_colour, n_rate))

    time_keep = Time(utime.ticks_ms())
    time_keep.prev_time = utime.ticks_ms()

    disp_top = LoopSequence(line_1, (n_colour, BLANK))
    disp_mid = LoopSequence(line_2, (n_colour, BLANK))
    disp_bot = LoopSequence(line_3, (n_colour, BLANK))

    while True:
        turn_on(np, disp_top.get_next_pixels(), disp_top.get_next_colour())
        turn_on(np, disp_mid.get_next_pixels(), disp_mid.get_next_colour())
        turn_on(np, disp_bot.get_next_pixels(), disp_bot.get_next_colour())
        time.sleep(n_rate)

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

