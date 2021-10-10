import neopixel
import time
import utime
import uasyncio as asyncio
from main import UserInput
from Classes import Queue, LoopSequence, Colour

# Colours
RED = Colour((255, 0, 0), "red")
ORANGE = Colour((255, 128, 0), "orange")
YELLOW = Colour((255, 255, 0), "yellow")
DARK_GREEN = Colour((0, 102, 0), "dark green")
GREEN = Colour((0, 204, 0), "green")
LIGHT_GREEN = Colour((102, 255, 102), "light green")
DARK_BLUE = Colour((0, 0, 102), "dark blue")
BLUE = Colour((0, 0, 255), "blue")
LIGHT_BLUE = Colour((102, 178, 255), "light blue")
BLANK = Colour((0, 0, 0), "blank")
GREY = Colour((96, 96, 96), "grey")

# layers
circle_1 = [9, 13, 14, 19]
circle_2 = [1, 3, 4, 8, 10, 12, 15, 18, 20, 22]
circle_3 = [0, 2, 5, 6, 7, 11, 16, 17, 21]

# Horizontal Lines
line_1 = [[None], [22], [23, 19], [18], [17, 15], [16], [None]]
line_2 = [[21], [20, 12], [13], [14, 9], [8], [7, 5], [6]]
line_3 = [[None], [11], [10, 2], [3], [4, 1], [0], [None]]


def turn_on(np, stage, colour):
    for pixel in stage:
        if pixel is None:
            continue
        np[pixel] = colour.rgb
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

def do_row_cycle(main_queue, queue, colours):
    colour_rate, row_queue = queue
    if row_queue.get_current().completed_cycle():
        # print("row %s completed a cycle" % row_queue.get_current().name)
        colour, rate = colour_rate
        if row_queue.at_last_index():
            # cycled colour through all rows, time to remove
            print("\trow {row}, {colour} cycled through".format(row=row_queue.name, colour=colour_rate[0]))
            main_queue.pop()
            if colour[0].priority:
                make_only_priority(colours, None)
            print("Removing from command queue")
            print("Command Queue (" + str(main_queue.get_size()) + "): " + str(main_queue))
            # row_queue.restart()
        else:
            # pass colour onto next row
            row = row_queue.get_next()
            if not row.contains_priority():
                print("\tSetting colour %s to row %s" % (str(colour), row.name))
                row.set_color_rate(colour, rate)

def check_colour_pass(queue: Queue, colours):
    # check if there are items in the colour queue to cycle thru
    if queue.get_size() != 0:
        do_row_cycle(queue, queue.get_current(), colours)
        if queue.get_size() > 1:
            if queue.get_size() > 2:
                # update the next in line
                queue.move_item_forward(queue.items[2])
                queue.get_after_next()[1].restart()
            # start next in line
            # print("get_after_next(): " + str(queue.get_after_next()))
            do_row_cycle(queue, queue.get_after_next(), colours)

def cycle_rows(rows, np):
    for row in rows:
        if row.time_to_cycle():
            if row.pixels.at_last_index():
                turn_on(np, row.pixels.get_next(), row.colours.get_next())
            else:
                turn_on(np, row.pixels.get_next(), row.colours.get_current())

def turn_display_off(np, pixel_count):
    for pixel in range(pixel_count):
        np[pixel] = (0, 0, 0)
    np.write()

def make_only_priority(colours, colour):
    print("make only priority " + str(colour))
    for col in colours:
        col.remove_priority()
    if colour is not None:
        colour.make_priority()

def animation_idea_1(pin, user: UserInput):
    # while True:
    #     try:
    np = neopixel.NeoPixel(pin, 24)

    og_colours = (BLUE, LIGHT_BLUE, GREEN, YELLOW, ORANGE, RED)
    levels = (1, 2, 3, 4, 5, 6)
    colours = list(zip(og_colours, create_blank_list(len(og_colours))))
    rate_list = create_rate_list(1, 0.0005, len(colours))
    colour_rate_list = list(zip(colours, rate_list, levels))
    colour_rate_list = Queue(colour_rate_list, "colour_rate", restrict=True)
    start_colour_rate = (BLUE, BLANK), 1

    top = LoopSequence(line_1, start_colour_rate[0], "top", rate=start_colour_rate[1])
    mid = LoopSequence(line_2, start_colour_rate[0], "middle", rate=start_colour_rate[1])
    bot = LoopSequence(line_3, start_colour_rate[0], "bottom", rate=start_colour_rate[1])

    command_queue = Queue(None, "commands", max_size=4)
    current_level = 1
    utime.sleep(1)

    while True:
        # check for user input
        await asyncio.sleep_ms(0)
        user_read = await user.read_input()
        user.reset_input()
        if user_read == "OK":
            continue

        if user_read is not None:
            try:
                # print("user_read: " + user_read)
                new_level = int(user_read)

            except ValueError:
                # got an invalid input, ignore
                print("Tried to parse {" + user_read + "}")
                continue
            if new_level not in levels:
                continue
            print("Command Queue (" + str(command_queue.get_size()) + "): " + str(command_queue))
            print("current level: " + str(current_level) + " new level " + str(new_level))
            while current_level != new_level:
                print("current level: " + str(current_level))
                if new_level > current_level:
                    n_colour, n_rate, n_level = colour_rate_list.get_next()
                    print("Adding colour %s to queue" % str(n_colour))
                    command_queue.add_item(((n_colour, n_rate), Queue((bot, mid, top), "inc_row")))
                    print("Command Queue (" + str(command_queue.get_size()) + "): " + str(command_queue))
                    current_level = n_level
                else:
                    n_colour, n_rate, n_level = colour_rate_list.get_prev()
                    print("Adding colour %s to queue" % str(n_colour))
                    command_queue.add_item(((n_colour, n_rate), Queue((top, mid, bot), "dec_row")))
                    print("Command Queue (" + str(command_queue.get_size()) + "): " + str(command_queue))
                    current_level = n_level
                make_only_priority(og_colours, n_colour[0])

            if command_queue.get_size() == 1:
                # start queue
                start_colour_rate, start_rows = command_queue.get_first()
                start_colour, start_rate = start_colour_rate
                start_row = start_rows.get_first()
                command_queue.start = False
                start_row.set_color_rate(start_colour, start_rate)
            await user.reset_input()

        check_colour_pass(command_queue, og_colours)
        cycle_rows((top, mid, bot), np)
        # except:
        #     continue


def run_circle(pin):
    np = neopixel.NeoPixel(pin, 24)
    stages = (circle_1, circle_2, circle_3)
    colours = (RED, GREEN, BLUE)
    for index in range(3):
        # set lights to red
        turn_on(np, stages[index], colours[index])
        time.sleep(3)
        turn_off(np, stages[index])

