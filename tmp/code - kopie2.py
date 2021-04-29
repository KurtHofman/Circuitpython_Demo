import time
import ssl
import socketpool
import wifi
import rtc
import adafruit_requests
import adafruit_minimqtt.adafruit_minimqtt as MQTT

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

### Setup MQTT
# Setup feeds
photocell_feed = secrets["aio_username"] + "/feeds/photocell"
onoff_feed = secrets["aio_username"] + "/feeds/onoff"
# Setup callbacks
def connected(client, userdata, flags, rc):
    print("Connected to Adafruit IO ! Listening for topic changes on %s" % onoff_feed)
    client.subscribe(onoff_feed)
def disconnected(client, userdata, rc):
    print("Disconnected from Adafruit IO !")
def message(client, topic, message):
    print("New message on topic {0}: {1}".format(topic, message))
# Setup mqtt-client
pool = socketpool.SocketPool(wifi.radio)
mqtt_client = MQTT.MQTT(
    broker=secrets["aio_broker"],
    port=secrets["aio_port"],
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message
print("Connecting to Adafruit IO ...")
mqtt_client.connect()

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
    print(f"System Time: {r.datetime}")
else:
    print("Setting time failed")

# TIME_URL = "https://io.adafruit.com/api/v2/%s/integrations/time/strftime?x-aio-key=%s" % (secrets["aio_username"], secrets["aio_key"])
# TIME_URL += "&fmt=%25d/%25m/%25Y+%25H%3A%25M%3A%25S"
# pool = socketpool.SocketPool(wifi.radio)
# requests = adafruit_requests.Session(pool, ssl.create_default_context())
# print("Fetching text from", TIME_URL)
# response = requests.get(TIME_URL)
# print("-" * 40)
# print(response.text)
# print("-" * 40)
# now=time.localtime(time.time())
# print("It is currently {}/{}/{} at {}:{}:{} UTC".format(now.tm_mon, now.tm_mday, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
# print("-" * 40)

# Setup variables, ...
photocell_val = 0

####################
### PROGRAM-LOOP ###
####################

while True:
    now=r.datetime
    print("-" * 40)
    print("It is currently {}/{}/{} at {}:{}:{} CEST".format(now.tm_mon, now.tm_mday, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
    print("-" * 40)
    # Poll the message queue
    mqtt_client.loop()
    # Send a new message
    print("Sending photocell value: %d..." % photocell_val)
    # mqtt_client.publish(photocell_feed, photocell_val)
    print("Sent!")
    print("=" * 40)
    photocell_val += 1
    time.sleep(5)


