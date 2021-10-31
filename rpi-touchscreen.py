#!/usr/bin/env python
import time
import subprocess
import paho.mqtt.client as mqtt
from urllib.request import urlopen
from urllib.error import URLError

subprocess.call("DISPLAY=:0 xset s off", shell=True)
subprocess.call("DISPLAY=:0 xset -dpms", shell=True)

screenOn = True

# Workaround
def wait_for_internet_connection():
    while True:
        try:
            response = urlopen('https://google.com',timeout=1)
            return
        except URLError:
            pass

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        client.subscribe("dashboard/rpi1/#")
    else:
        print("Bad connection Returned code=",rc)

screenOn = True

def on_message(client, userdata, msg):
    payload = str(msg.payload.decode("utf-8"))
    topic = msg.topic
    print("Received message '" + payload + "' on topic '"
        + topic + "' with QoS " + str(msg.qos))

    if topic == 'dashboard/rpi1/set':
        print("Set message received")
        values = payload.split(',')
        state = values[0]
        if state == 'on':
            screenOn = True
            subprocess.call("DISPLAY=:0 xscreensaver-command -deactivate", shell=True)
        else:
            screenOn = False
            subprocess.call("DISPLAY=:0 xscreensaver-command -activate", shell=True)
        getStatus()
    elif topic == 'dashboard/rpi1/reload':
        subprocess.call("sudo killall kiosk.sh && sudo service lightdm restart", shell=True)

def getStatus():
    topic = "dashboard/rpi1/status"
    if screenOn:
        state = 'on'
    else:
        state = 'off'
    brightness = 100
    payload = state+","+str(brightness)
    print("Publishing " + payload + " to topic: " + topic + " ...")
    client.publish(topic, payload, 0, True)

wait_for_internet_connection()
mqtt.Client.connected_flag=False#create flag in class
#broker="mqtt://homeassistant.local:1883"
broker="homeassistant.local"
client = mqtt.Client("dashboard")
client.username_pw_set('********', '**********')            #create new instance
client.on_connect=on_connect  #bind call back function
client.on_message=on_message
client.loop_start()
print("Connecting to broker ",broker)
client.connect(broker)      #connect to broker
while not client.connected_flag: #wait in loop
    print("In wait loop")
    time.sleep(1)
while 1:
    try:
        getStatus()

    except Exception as e:
        print("exception")
        log_file=open("log.txt","w")
        log_file.write(str(time.time())+" "+e.__str__())
        log_file.close()

    print("")
    time.sleep(10)
