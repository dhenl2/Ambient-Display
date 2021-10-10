import utime

class Queue:
    def __init__(self, items, name, restrict=False, max_size=1000):
        if items is None:
            self.items = list()
        else:
            self.items = items
        self.index = 0
        self.restrict = restrict
        self.start = True
        self.name = name
        self.max_size = max_size

    def __repr__(self):
        return "Queue: " + str(self.items)

    def __eq__(self, other):
        if not isinstance(other, Queue):
            return False
        return self.items == other.items and self.index == other.index and self.restrict == other.restrict and \
               self.start == other.start and self.name == other.name and self.max_size == other.max_size

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

    def move_item_forward(self, item):
        item_index = self.items.index(item)
        popped = self.items.pop(item_index - 1)
        print("Popped: " + str(popped))

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
        if self.get_size() >= self.max_size:
            # replace the most recently added item
            self.items[self.get_size() - 1] = item
        else:
            self.items.append(item)
        # print("\titems in %s is now %s" % (self.name, self.items))

    def pop(self):
        popped = self.items.pop(0)

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

    def __repr__(self):
        print("LoopSequence: " + self.name)

    def __eq__(self, other):
        if not isinstance(other, LoopSequence):
            return False
        return self.pixels == other.pixels and self.colours == other.colours and self.name == other.name and \
               self.rate == other.rate and self.time == other.time

    def set_color_rate(self, colours, rate):
        self.colours = Queue(colours, "colours")
        self.rate = rate

    def contains_priority(self):
        for colour in self.colours.items:
            if colour.priority:
                return True
        return False

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

class Colour:
    def __init__(self, rgb, name):
        self.rgb = rgb
        self.name = name
        self.priority = False

    def __repr__(self):
        return self.name

    def make_priority(self):
        self.priority = True

    def remove_priority(self):
        self.priority = False

    def __eq__(self, other):
        if not isinstance(other, Colour):
            return False
        return self.rgb == other.rgb and self.name == other.name

class Time:
    def __init__(self):
        self.prev_time = 0
        self.curr_time = 0
        self.start_time = utime.ticks_ms()

    def __eq__(self, other):
        if not isinstance(other, Time):
            return False

        return self.prev_time == other.prev_time and self.curr_time == other.curr_time and \
               self.start_time == other.start_time

    def get_dt(self):
        self.curr_time = utime.ticks_ms()
        return (self.curr_time - self.prev_time) / 1000

    def get_elapsed(self):
        self.curr_time = utime.ticks_ms()
        return (self.curr_time - self.start_time) / 1000

    def start_timer(self):
        self.prev_time = utime.ticks_ms()
