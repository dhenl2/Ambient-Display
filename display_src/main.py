import time
import display as dp
from machine import Pin
import uasyncio
from uasyncio import Lock

class UserInput:
    def __init__(self, lock):
        self.read = None
        self.lock = lock

    async def read_input(self):
        await self.lock.acquire()
        result = self.read
        self.lock.release()

    def add_input(self, new_input):
        await self.lock.acquire()
        self.read = new_input
        self.lock.release()

    def reset_input(self):
        await self.lock.acquire()
        self.read = None
        self.lock.release()


async def read_user_input(user):
    while True:
        val = input("Choose to (inc, dec): ")
        user.add_input(val)
        await uasyncio.sleep(2)


def main():
    time.sleep(2)
    print("Starting main()")
    dp_pin = Pin(13)  # adjust plz
    user = UserInput(Lock())
    loop = uasyncio.get_event_loop()
    loop.create_task(dp.animation_idea_1(user, dp_pin))
    loop.create_task(read_user_input(user))
    loop.run_forever()
    dp.animation_idea_1(user, dp_pin)


if __name__ == "__main__":
    # uasyncio.run(main())
    dp_pin = Pin(13)  # adjust plz
    # user = UserInput(Lock())
    dp.animation_idea_1(dp_pin)