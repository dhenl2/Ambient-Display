import machine
import utime
import math

pot = machine.ADC(0)

def read_deb():
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

    # db reading calculation taken from:
    # https://forums.adafruit.com/viewtopic.php?f=8&t=100462
    peak_to_peak = signal_max - signal_min
    volts = (peak_to_peak * 3.3) / 1024
    first = (math.log(volts / 0.00631) / math.log(10)) * 20     # converts natural log to log10
    second = first + 94 - 44 - 25
    print("dB reading: " + str(second) + "dB")
    return second
