import machine
from machine import Pin
from time import sleep
import utime

pot = machine.ADC(0)


def read_freq(pin):
    sample_window = 50        # 50ms = 20Hz
    start_time = utime.ticks_ms()
    signal_max = 0
    signal_min = 1024

    # collect data for 50ms
    while (utime.ticks_ms() - start_time) < sample_window:
        sample = pot.read()
        if sample < 1024:
            if sample > signal_max:
                signal_max = sample
            elif sample < signal_min:
                signal_min = sample

    peak_to_peak = signal_max - signal_min
    volts = (peak_to_peak * 5.0) / 1024
    print(volts)



def read_pin(pin):
    pot_value = pot.read()
    print(pot_value)
    sleep(0.1)