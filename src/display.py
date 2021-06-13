import neopixel
from machine import Pin
import time

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
line_1 = [[22], [23, 19], [18], [17, 15], [16]]
line_2 = [[21], [20, 12], [13], [14, 9], [8], [7, 5], [6]]
line_3 = [[11], [10, 2], [3], [4, 1], [0]]


class LoopSequence:
    def __init__(self, pixels, colours):
        self.pixels = pixels
        self.colours = colours
        self.colour_index = 0
        self.pixel_index = 0
        self.first_pixel = True
        self.first_colour = True

    def get_next_pixels(self):
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


def run_sequence(pin):
    np = neopixel.NeoPixel(pin, 24)
    for pixel in range(24):
        np[pixel] = RED
        np.write()
        time.sleep(2)
        np[pixel] = BLANK
        np.write()


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


def turn_on(np, stage, colour):
    for pixel in stage:
        np[pixel] = colour
    np.write()


def turn_off(np, stage):
    for pixel in stage:
        np[pixel] = (0, 0, 0)
    np.write()


def run_circle(pin):
    np = neopixel.NeoPixel(pin, 24)
    stages = (circle_1, circle_2, circle_3)
    colours = (RED, GREEN, BLUE)
    for index in range(3):
        # set lights to red
        turn_on(np, stages[index], colours[index])
        time.sleep(3)
        turn_off(np, stages[index])

