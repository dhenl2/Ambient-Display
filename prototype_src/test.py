import utime
import neopixel
from machine import Pin
import time


# Pins in Use
pin_pixels = Pin(5)


def flash(timer, led):
    count = 0
    while count < timer:
        led.on()
        utime.sleep_ms(50)
        led.off()
        utime.sleep_ms(50)
        count += 1
    led.on()


def neo_pixel_test(np):
    # np = neopixel.NeoPixel(pin_pixels, 24)
    for pixel in range(0, 24):
        np[pixel] = (255, 0, 0)
        np.write()
        time.sleep(2)
        np[pixel] = (0, 0, 0)


def flash_test():
    led = Pin(2, Pin.OUT)
    enabled = False
    while True:
        for step in range(10):
            flash(step, led)
            utime.sleep(2)


if __name__ == '__main__':
    while True:
        # neo_pixel_test()
        # run_circle()
