#!/usr/bin/env python
import sys
from Server import start_server, ServerInfo
from Client import client_thread
from threading import Lock, Thread
import signal
import time
import os
from pa1010d import PA1010D
from gps_local_time import get_local_time
import argparse

directory = "/home/pi/Python/Log/"


def run_server(server):
    sock = start_server("0.0.0.0", 8123)
    if server.dev:
        dev_input_thread = Thread(target=server.prompt_new_level, args=(), daemon=True)
        server.threads.append(dev_input_thread)
        dev_input_thread.start()

    while True:
        print(f"Waiting for a connection...")
        con, addr = sock.accept()
        print(f"Connected to {addr}")
        thread_id = Thread(target=client_thread, args=(con, server,), daemon=True)
        thread_id.start()
        server.threads.append(thread_id)


def set_local_time():
    gps = PA1010D()
    while True:
        # await gps lock and date and time
        gps.update()
        if (gps.timestamp is not None) and (gps.datestamp is not None):
            break
        time.sleep(2)
    print("GPS lock acquired")
    current_date_time = get_local_time(gps.timestamp, gps.datestamp).isoformat(sep=" ")
    print(f"Setting date and time to {current_date_time}")
    os.system(f"sudo date -s'{current_date_time}'")
    return


def main(args):
    def stop_server(signal_no, frame):
        print("Received signal " + str(signal_no))
        server.quit_clients()
        for thread in server.threads:
            # got 5s to come back properly or your getting a smack
            thread.join(5)
        server.activity_level.close_log_files()
        sys.exit()

    def routine_calibration():
        while True:
            time.sleep(60 * 10)  # run this every 3hrs
            server.set_clients_pause(True)
            server.activity_level.create_activity_levels()
            server.set_clients_pause(False)

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGQUIT, stop_server)
    signal.signal(signal.SIGUSR1, routine_calibration)

    lock = Lock()
    server = ServerInfo(lock, args.dev)

    server_thread = Thread(daemon=True, target=run_server, args=(server,))
    set_date_time_thread = Thread(daemon=True, target=set_local_time)
    set_date_time_thread.start()
    server_thread.start()
    routine_calibration()


def create_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", required=False, help="Development mode to control display levels", action="store_true")
    return parser


if __name__ == "__main__":
    args_parser = create_args()
    main(args_parser.parse_args())
