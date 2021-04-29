import time
import board
import adafruit_ltr390
import feathers2

i2c = board.I2C()
ltr = adafruit_ltr390.LTR390(i2c)

while True:
    feathers2.led_blink()
    print("UV:", ltr.uvs, "\t\tAmbient Light:", ltr.light)
    print("UVI:", ltr.uvi, "\t\tLux:", ltr.lux)
    time.sleep(1.0)
