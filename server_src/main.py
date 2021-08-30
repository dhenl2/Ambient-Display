import sys
from _thread import *
from Server import start_server, ServerInfo
from Client import client_thread
from threading import Lock, Thread
import signal
import time

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
    lock = Lock()
    server = ServerInfo(lock)
    calibrate_now = False

    def stop_server(signal_no, frame):
        print("Received signal " + str(signal_no))
        server.quit_clients()
        for thread in server.threads:
            # got 5s to come back properly or your getting a smack
            thread.join(5)
        server.activity_level.log_file.close()
        sys.exit()

    def time_to_calibrate(signal_no, frame):
        print("Received signal " + str(signal_no))
        print("Triggered a calibration")
        calibrate_now = True

    def routine_calibration():
        # calibrate every 1hr or when calibrate_now is set
        last_time = time.time()
        interval = 60 * 60
        while True:
            if (((time.time() - last_time) > interval) and server.activity_level.calibrate_again) or calibrate_now:
                # pause all clients from adding new data
                server.set_clients_pause(True)
                server.activity_level.create_activity_levels()
                server.set_clients_pause(False)
                calibrate_now = False
            time.sleep(3)

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGQUIT, stop_server)
    signal.signal(signal.SIGUSR1, routine_calibration())

    start_new_thread(run_server, (server, ))
    routine_calibration()



if __name__ == "__main__":
    main()
