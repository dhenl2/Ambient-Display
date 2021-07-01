import display as dp
from machine import Pin

if __name__ == "__main__":
    dp_pin = Pin(13)        # adjust plz
    dp.run_line_animation()