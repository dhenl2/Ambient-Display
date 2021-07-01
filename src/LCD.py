import time
import machine
from esp8266_i2c_lcd import I2cLcd


def init_lcd():
    print("initialising LCD")
    sda = machine.Pin(4)
    scl = machine.Pin(5)
    i2c = machine.I2C(sda=sda, scl=scl)
    devices = i2c.scan()
    if len(devices) == 0:
        print("No I2C devices!")
        return
    for device in devices:
        print("Device " + str(device) + " is Hex " + hex(device))
        lcd = I2cLcd(i2c, int(hex(device), 0), 2, 16)
        lcd.backlight_off()
        time.sleep(0.5)
        lcd.backlight_on()
        display_text(lcd, str(hex(device)))
        time.sleep(2)
    exit(1)

    device_addr = 0x27
    lcd = I2cLcd(i2c, device_addr, 2, 16)
    lcd.putstr("Ready...")
    time.sleep(2)
    lcd.clear()
    return lcd


def display_text(lcd, text, clear=True):
    if clear:
        lcd.clear()
    lcd.putstr(text)

