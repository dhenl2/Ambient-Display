from machine import UART, Pin


def write_msg(msg):
    UART.write(msg)