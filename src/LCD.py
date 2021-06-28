import time
import machine
from lcd_api import LcdApi
from esp8266_i2c_lcd import I2cLcd


def lcd_test():
    sda = machine.Pin(4)
    scl = machine.Pin(5)
    i2c = machine.I2C(sda=sda, scl=scl)
    devices = i2c.scan()
    device_addr = 0x27
    lcd = I2cLcd(i2c, device_addr, 2, 16)
    lcd.clear()
    lcd.putstr("We can now start")

