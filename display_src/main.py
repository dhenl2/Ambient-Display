import time
import display as dp
from machine import Pin
import uasyncio as asyncio
from uasyncio import Lock

class UserInput:
    def __init__(self, lock):
        self.read = None
        self.lock = lock

    async def read_input(self):
        # print("reading user input")
        await self.lock.acquire()
        result = self.read
        self.lock.release()
        # print("finished reading user input")
        return result

    async def add_input(self, new_input):
        # print("adding user input")
        await self.lock.acquire()
        self.read = new_input
        self.lock.release()
        # print("finished adding user input")

    async def reset_input(self):
        await self.lock.acquire()
        self.read = None
        self.lock.release()

async def read_user_input(user):
    while True:
        # val = await ainput("Choose to (inc, dec): ")
        if val != "inc" or val != "dec":
            print("Not a valid input")
        else:
            user.add_input(val)
        await asyncio.sleep(2)


async def pretend_user_input(user):
    print("Pretending to be a user")
    user_inputs = ['inc', 'inc', 'inc', 'inc', 'inc', 'dec', 'dec', 'dec']
    # user_inputs = ['inc', 'inc']
    from display import Time
    timer = Time()
    timer.start_timer()
    for i in range(len(user_inputs)):
        print("Adding user input " + user_inputs[i])
        await user.add_input(user_inputs[i])
        await asyncio.sleep(20)
    print("Finished adding user inputs")


def main():
    time.sleep(2)
    print("Starting main()")
    dp_pin = Pin(13)  # adjust plz
    user = UserInput(Lock())
    loop = asyncio.get_event_loop()
    loop.create_task(dp.animation_idea_1(dp_pin, user))
    loop.create_task(pretend_user_input(user))
    loop.run_forever()
    # dp.animation_idea_1(dp_pin, user)


if __name__ == "__main__":
    asyncio.run(main())
    # dp_pin = Pin(13)  # adjust plz
    # user = UserInput(Lock())
    # dp.animation_idea_1(dp_pin)