from datetime import datetime
import struct

import paho.mqtt.client as mqtt

from calc_crc import crc8

fd = open('data.bin' ,'wb')

#deg
def get_direction(bytes_vals):
    dir = bytes_vals[6]
    if bytes_vals[3] & 0b100:
        dir += 256
    return dir

#F
def get_temperature(bytes_vals):
    return (bytes_vals[9] * 256 + bytes_vals[10] - 33168 ) / 10.

WIND_CONV_FACTOR = 0.224

#MPH
def get_avr_wind(bytes_vals):
    return bytes_vals[4] * 0.224

#MPH
def get_gust_wind(bytes_vals):
    return bytes_vals[5] * 0.224

#inch
def rain_measure(bytes_vals):
    return ( bytes_vals[7] * 256+bytes_vals[8]) * 0.0039336


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
    if crc8(data[:-1]) == data[-1]:
        print(datetime.now() ,{'temp': get_temperature(data),
                'humidity': data[11],
                'wind_dir': get_direction(data),
                'avr_wind': get_avr_wind(data),
                'gust_wind': get_gust_wind(data),
                'rain': rain_measure(data),
                 })
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