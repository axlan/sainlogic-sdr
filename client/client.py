from datetime import datetime
import struct
import time
import sys

import paho.mqtt.client as mqtt

from .wunder_api import WUndergroundUploadAPI

import sys  
sys.path.insert(0, 'gr-sainlogic/python')

from sainlogic_parser import get_measurements

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
    data = struct.pack('I', int(time.time())) + data
    userdata['fd'].write(data)
    userdata['fd'].flush()
    measurements = get_measurements(parsed)
    #print(parsed)
    if measurements is not None:
        print(datetime.now() ,measurements)
        ret = userdata['uploader'].send_sainlogic(measurements)
        if ret != 'success':
            print(f'Upload failed: {ret}')
    else:
        print(datetime.now() ,'CRC Failure')

def main():

    if len(sys.argv) != 3:
        print('usage: python -m client.client STATION_ID STATION_KEY')
        exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fd = open(f'out/sainlog_log_{timestamp}.bin' ,'wb')
    uploader = WUndergroundUploadAPI(sys.argv[1], sys.argv[2])
    userdata = {
        'fd': fd,
        'uploader': uploader
    }

    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("192.168.1.110", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()


if __name__ == "__main__":
    main()
