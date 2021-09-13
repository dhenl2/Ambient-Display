#!/usr/bin/env python
import sys
from Server import start_server, ServerInfo
from Client import client_thread
from threading import Lock, Thread
import signal
import time
import os

directory = "/home/pi/Python/Log/"

def run_server(server):
    sock = start_server("0.0.0.0", 8123)

    while True:
        print(f"Waiting for a connection...")
        con, addr = sock.accept()
        print(f"Connected to {addr}")
        thread_id = Thread(target=client_thread, args=(con, server,), daemon=True)
        thread_id.start()
        server.threads.append(thread_id)

def main():
    def stop_server(signal_no, frame):
        print("Received signal " + str(signal_no))
        server.quit_clients()
        for thread in server.threads:
            # got 5s to come back properly or your getting a smack
            thread.join(5)
        server.activity_level.close_log_files()
        sys.exit()

    def time_to_calibrate(signal_no, frame):
        print("Received signal " + str(signal_no))
        print("Triggered a calibration")
        server.calibrate_now = True

    def routine_calibration():
        shed_open = 7
        shed_close = 14
        open_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        def shed_closed():
            try:
                current_hour = int(time.strftime("%H"))
                today = time.strftime("%A")
            except ValueError:
                return False
            return current_hour > shed_close or current_hour < shed_open

        def shed_is_open():
            try:
                current_hour = int(time.strftime("%H"))
                today = time.strftime("%A")
            except ValueError:
                return False
            return today in open_days and (shed_open <= current_hour <= shed_close)

        def log_files_available():
            return len(os.listdir(directory)) > 2

        start_timer = time.time()
        leave_on = False
        while True:
            if shed_closed() or not leave_on:
                print(f"closing shed")
                server.set_display_clients(False)
                if server.activity_level.calibrate_again and log_files_available() or server.calibrate_now:
                    # pause all clients from adding new data
                    print("It's now past the shed close time. Time to calibrate")
                    server.set_clients_pause(True)
                    server.activity_level.create_activity_levels()
                    server.set_clients_pause(False)
            # elif shed_is_open():
            # print(f"Current timer: {time.time() - start_timer}")
            # if time.time() - start_timer > 30:
            #     print("opening shed")
            #     server.set_display_clients(True)
            #     leave_on = True
            time.sleep(60 * 60 * 2)     # run this every 3hrs

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGQUIT, stop_server)
    signal.signal(signal.SIGUSR1, routine_calibration)

    lock = Lock()
    server = ServerInfo(lock)

    server_thread = Thread(daemon=True, target=run_server, args=(server, ))
    # print("Starting server thread")
    server_thread.start()
    routine_calibration()



if __name__ == "__main__":
    main()
