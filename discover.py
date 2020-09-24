import paho.mqtt.client as mqtt
from Controller import Controller
from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch
import json
import logging
import threading
import time

HOST = "192.168.0.2"
USER = "Coelhomatias"
PASSWORD = "lf171297"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("controller/discover/#", 1)

# The callback for when a PUBLISH message is received from the server.
def on_discover_switch(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print("Just discovered switch: " + parsed["unique_id"])
    control.add_component(Switch(parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["command_topic"]))

def on_discover_sensor(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print("Just discovered sensor: " + parsed["unique_id"])
    control.add_component(Sensor(parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["unit_of_measurement"]))

def on_discover_blinds(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print("Just discovered blinds: " + parsed["unique_id"])
    control.add_component(Blinds(parsed["name"], parsed["unique_id"], parsed["position_topic"], parsed["command_topic"]))


if __name__ == "__main__":
    
    control = Controller("blind1", "2c3ae8364cb5", "blinds1/status", HOST, USER, PASSWORD)
    client = mqtt.Client()
    client.username_pw_set(username=USER,password=PASSWORD)
    client.on_connect = on_connect
    client.message_callback_add("controller/discover/switch/#", on_discover_switch)
    client.message_callback_add("controller/discover/sensor/#", on_discover_sensor)
    client.message_callback_add("controller/discover/cover/#", on_discover_blinds)

    client.connect(HOST)


    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()

