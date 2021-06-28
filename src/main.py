# from display import run_circle, run_sequence, run_line_animation
# from vibration import write_msg
# from microphone import read_pin, read_freq
import time
from machine import UART, Pin
import socket
from LCD import init_lcd, display_text
from hcsr04 import HCSR04

display_pin = Pin(4)        # D2
microphone_pin = Pin(5, Pin.IN)     # D1
vibration_pin = Pin(14)     # D5


def test_server():
    host = "127.0.0.1"
    port = 1233

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen()
        client, addr = sock.accept()
        with client:
            print("Connected by " + addr)
            while True:
                data = client.recv(1024)
                if not data:
                    break
                # client.send(byte("received your message boss", "utf-8"))


if __name__ == '__main__':
    while True:
        lcd = init_lcd()
        if lcd is None:
            exit(1)
        sensor = HCSR04(trigger_pin=1, echo_pin=3)
        while True:
            distance = sensor.distance_cm()
            display_text(lcd, "Distance: " + str(int(distance)) + "cm")
            time.sleep(0.5)
