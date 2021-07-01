import microphone as mic
from machine import Pin

if __name__ == "__main__":
    mic_pin = Pin(5, Pin.IN)
    mic.read_pin(mic_pin)
    mic.read_freq(mic_pin)