from pa1010d import PA1010D
import time
import datetime
import pytz

gps = PA1010D()


def get_local_time(timestamp, datestamp):
    timezone = pytz.timezone("Australia/Brisbane")
    utc_time = datetime.datetime.combine(datestamp, timestamp)
    utc_time = pytz.UTC.localize(utc_time)
    current_time = utc_time.astimezone(timezone)
    current_time = current_time.replace(tzinfo=None)
    return current_time


def main():
    while True:
        time.sleep(1)
        gps.update()
        if gps.timestamp is not None and gps.datestamp is not None:
            print(get_local_time(gps.timestamp, gps.datestamp).isoformat(sep=" "))


if __name__ == "__main__":
    main()
