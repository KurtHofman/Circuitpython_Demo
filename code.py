import time
import ssl
import socketpool
import wifi
import rtc
import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_requests
import adafruit_scd30
import adafruit_ssd1327
from adafruit_lc709203f import LC709203F
from adafruit_pm25.i2c import PM25_I2C

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

#############
### SETUP ###
#############

### Setup WiFI
print("Connecting to %s ..." % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s !" % secrets["ssid"])
print("My IP : %s" % wifi.radio.ipv4_address)
pool = socketpool.SocketPool(wifi.radio)

# Setup time
r = rtc.RTC()
requests = adafruit_requests.Session(pool, ssl.create_default_context())
response = requests.get("http://worldtimeapi.org/api/timezone/Europe/Brussels")
# {"abbreviation":"CEST","client_ip":"84.198.207.226","datetime":"2021-04-26T10:38:58.027337+02:00","day_of_week":1,"day_of_year":116,"dst":true,"dst_from":"2021-03-28T01:00:00+00:00","dst_offset":3600,"dst_until":"2021-10-31T01:00:00+00:00","raw_offset":3600,"timezone":"Europe/Brussels","unixtime":1619426338,"utc_datetime":"2021-04-26T08:38:58.027337+00:00","utc_offset":"+02:00","week_number":17}
if response.status_code == 200:
    utc_offset=3600
    if response.json()['utc_offset'] == '+02:00':
        utc_offset=7200
    r.datetime = time.localtime(response.json()['unixtime']+utc_offset)
    # print(f"System Time: {r.datetime}")
else:
    print("Setting time failed")

# Setup Adafruit LC709203F LiPoly / LiIon Fuel Gauge and Battery Monitor
sensor = LC709203F(board.I2C())

# Setup Adafruit PMSA003I Air Quality Breakout
reset_pin = None
pm25 = PM25_I2C(board.I2C(), reset_pin)

# Setup Adafruit LTR390 UV Sensor
#ltr = adafruit_ltr390.LTR390(board.I2C())

# Setup Adafruit Grayscale 1.5" 128x128 OLED Display
WIDTH = 128
HEIGHT = 128
BORDER = 8
FONTSCALE = 1
displayio.release_displays()
display_bus = displayio.I2CDisplay(board.I2C(), device_address=0x3D)
display = adafruit_ssd1327.SSD1327(display_bus, width=128, height=128)
splash = displayio.Group(max_size=10)
display.show(splash)
color_bitmap = displayio.Bitmap(
    display.width - BORDER * 2, display.height - BORDER * 2, 1
)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF
bg_sprite = displayio.TileGrid(
    color_bitmap, pixel_shader=color_palette, x=BORDER, y=BORDER
)
splash.append(bg_sprite)
inner_bitmap = displayio.Bitmap(
    display.width - BORDER * 4, display.height - BORDER * 4, 1
)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x888888
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER * 2, y=BORDER * 2
)
splash.append(inner_sprite)
text = "Hello"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF)
text_width = text_area.bounding_box[2] * FONTSCALE
text_group = displayio.Group(
    max_size=10,
    scale=FONTSCALE,
    x=display.width // 2 - text_width // 2,
    y=display.height // 2,
)
text_group.append(text_area)
splash.append(text_group)

# Setup Adafruit SCD-30 - NDIR CO2 Temperature and Humidity Sensor
scd = adafruit_scd30.SCD30(board.I2C())
# scd.temperature_offset = 10
print("Temperature offset:", scd.temperature_offset)
# scd.measurement_interval = 4
print("Measurement interval:", scd.measurement_interval)
# scd.self_calibration_enabled = True
print("Self-calibration enabled:", scd.self_calibration_enabled)
# scd.ambient_pressure = 1100
print("Ambient Pressure:", scd.ambient_pressure)
# scd.altitude = 100
print("Altitude:", scd.altitude, "meters above sea level")
# scd.forced_recalibration_reference = 409
print("Forced recalibration reference:", scd.forced_recalibration_reference)
print("")

# Setup variables, ...


####################
### PROGRAM-LOOP ###
####################

while True:
    now=r.datetime
    print("-" * 40)
    print("It is currently {}/{}/{} at {}:{}:{} CEST".format(now.tm_mon, now.tm_mday, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
    print("-" * 40)
    if scd.data_available:
        print("Data Available!")
        print("CO2:", scd.CO2, "PPM")
        print("Temperature:", scd.temperature, "°C")
        print("Humidity:", scd.relative_humidity, "%")
    print("-" * 40)
    try:
        aqdata = pm25.read()
        # print(aqdata)
    except RuntimeError:
        print("Unable to read from sensor, retrying...")
        continue
    print()
    print("Concentration Units (standard)")
    print("---------------------------------------")
    print("PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"]))
    print("Concentration Units (environmental)")
    print("---------------------------------------")
    print("PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"]))
    print("---------------------------------------")
    print("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
    print("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
    print("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
    print("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
    print("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
    print("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
    print("---------------------------------------")
    #print("UV Index:", ltr.uvi, "\t\tLux:", ltr.lux)
    print("=" * 40)

    text = "{}/{}/{} {}:{}:{}\n\r".format(now.tm_mon, now.tm_mday, now.tm_year,now.tm_hour, now.tm_min, now.tm_sec)
    text = text+"Battery: {} %\n\r".format(sensor.cell_percent)
    #text=text+"IP: {}\n\r".format(wifi.radio.ipv4_address)
    text=text+"CO2: {} PPM\n\r".format(scd.CO2)
    text=text+"PPM 25um: {}\n\r".format(aqdata["particles 25um"])
    text=text+"Temp: {} °C\n\r".format(scd.temperature)
    text=text+"Humidity: {} %\n\r".format(scd.relative_humidity)
    #text=text+"UV Index: {}\n\r".format(ltr.uvi)
    text_area = label.Label(terminalio.FONT, text=text)
    text_area.x = 10
    text_area.y = 10
    display.show(text_area)
    time.sleep(10)
    pass

