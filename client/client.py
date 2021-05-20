from datetime import datetime
import struct

import paho.mqtt.client as mqtt

import sys  
sys.path.insert(0, '/home/axlan/src/sainlogic-sdr/gr-sainlogic/python')

from sainlogic_parser import get_measurements

fd = open('out/data.bin' ,'wb')

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("weather_data")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    data = msg.payload
    # print(msg.topic+" "+str(msg.payload))
    parsed = struct.unpack('16B', data)
    print(parsed)
    fd.write(data)
    measurements = get_measurements(parsed)
    if measurements is not None:
        print(datetime.now() ,measurements)
    else:
        print(datetime.now() ,'CRC Failure')

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.110", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()