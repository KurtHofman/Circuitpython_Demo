import time
import board
from busio import I2C
import feathers2
import adafruit_dotstar
import adafruit_bme680

# Make sure the 2nd LDO is turned on
feathers2.enable_LDO2(True)

# Create a DotStar instance
dotstar = adafruit_dotstar.DotStar(
    board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.5, auto_write=True
)

# Create library object using our Bus I2C port
i2c = I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)

# You will usually have to add an offset to account for the temperature of
# the sensor. This is usually around 5 degrees but varies by use. Use a
# separate temperature sensor to calibrate this one.
temperature_offset = -5

# Create a colour wheel index int
color_index = 0

while True:
    # Get the R,G,B values of the next colour
    r, g, b = feathers2.dotstar_color_wheel(color_index)
    # Set the colour on the dotstar
    dotstar[0] = (r, g, b, 0.5)
    # Increase the wheel index
    color_index += 15
    # If the index == 255, loop it
    if color_index == 255:
        color_index = 0
    # Sleep for 15ms so the colour cycle isn't too fast
    print("\nTemperature: %0.1f C" % (bme680.temperature + temperature_offset))
    print("Humidity: %0.1f %%" % bme680.relative_humidity)
    print("Pressure: %0.3f hPa" % bme680.pressure)
    print("Gas: %d ohm" % bme680.gas)
    # Invert the internal LED state cycle
    feathers2.led_blink()
    time.sleep(1)
