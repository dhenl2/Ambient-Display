# from display import run_circle, run_sequence, run_line_animation
# from vibration import write_msg
# from microphone import read_pin, read_freq
from machine import Pin
import socket

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
    pass
    # lcd = init_lcd()
    # if lcd is None:
    #     print("no LCD")
    #     exit(1)
    # sensor_right = HCSR04(trigger_pin=5, echo_pin=4)
    # sensor_left = HCSR04(trigger_pin=14, echo_pin=12)
    # while True:
    #     print("Distance_left: " + str(int(sensor_left.distance_cm())) + "cm\n" +
    #           "Distance_right: " + str(int(sensor_right.distance_cm())) + "cm")
        # display_text(lcd, "Left: " + str(int(sensor_left.distance_cm())) + "cm")
        # lcd.move_to(0, 1)
        # display_text(lcd, "Right: " + str(int(sensor_right.distance_cm())) + "cm", False)
        # time.sleep(0.5)
