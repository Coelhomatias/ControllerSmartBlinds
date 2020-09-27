import paho.mqtt.client as mqtt
from cover_classes import Blinds, Sensor, Switch
import Controller as ctrl
from Device import Device
import multiprocessing as mp
from multiprocessing import Process, Value
import json
import time

HOST = "192.168.0.2"
USER = "Coelhomatias"
PASSWORD = "lf171297"
NUMBER_OF_SENSORS = 2
MAX_CTRLS = mp.cpu_count() + 4
number_of_processes = 0

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("controller/discover/#", 1)


def on_discover_switch(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print("Just discovered switch: " + parsed["unique_id"])
    device_id = (parsed["device"]["name"] + "_" +
                 parsed["device"]["identifiers"])
    if not device_id in nodes:
        create_device(parsed)

    nodes[device_id]["device"].set_Switch(Switch(
        parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["command_topic"]))

    check_if_finished(device_id)


def on_discover_sensor(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print("Just discovered sensor: " + parsed["unique_id"])
    device_id = (parsed["device"]["name"] + "_" +
                 parsed["device"]["identifiers"])
    if not device_id in nodes:
        create_device(parsed)

    nodes[device_id]["device"].add_Sensor(Sensor(
        parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["unit_of_measurement"]))

    check_if_finished(device_id)


def on_discover_blinds(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print("Just discovered blinds: " + parsed["unique_id"])
    device_id = (parsed["device"]["name"] + "_" +
                 parsed["device"]["identifiers"])
    if not device_id in nodes:
        create_device(parsed)

    nodes[device_id]["device"].set_Blinds(Blinds(
        parsed["name"], parsed["unique_id"], parsed["position_topic"], parsed["command_topic"]))

    check_if_finished(device_id)


def on_availability(client, userdata, msg):
    print("Availability message from topic,", msg.topic,
          "with payload:", msg.payload.decode())
    if msg.payload.decode() == "online":
        if not availability[msg.topic].value:
            availability[msg.topic].value = 1
    else:
        if availability[msg.topic].value:
            availability[msg.topic].value = 0


def create_device(dictionary):
    device_id = dictionary["device"]["name"] + \
        "_" + dictionary["device"]["identifiers"]
    node = {
        "device": Device(dictionary["device"]["name"], dictionary["device"]["identifiers"], dictionary["availability_topic"], NUMBER_OF_SENSORS),
    }
    nodes[device_id] = node
    print("Added new device to nodes with name:", device_id)


def check_if_finished(device_id):
    global number_of_processes
    run = Value("i", 1)
    if nodes[device_id]["device"].is_full() and not "process" in nodes[device_id] and number_of_processes < MAX_CTRLS:
        process = Process(target=ctrl.execution, args=(
            nodes[device_id]["device"], credentials, run))
        process.daemon = True
        process.start()
        number_of_processes += 1

        nodes[device_id]["process"] = process
        print("Added new process to nodes. The process was started")
        # Availability stuff, Implemented but not usefull
        availability[nodes[device_id]["device"].get_availability_topic()] = run
        client.subscribe(
            nodes[device_id]["device"].get_availability_topic(), 1)
        client.message_callback_add(
            nodes[device_id]["device"].get_availability_topic(), on_availability)


if __name__ == "__main__":

    nodes = dict()
    availability = dict()
    credentials = {
        "mqtt_host": HOST,
        "mqtt_user": USER,
        "mqtt_passwd": PASSWORD
    }

    client = mqtt.Client()
    client.username_pw_set(username=USER, password=PASSWORD)
    client.on_connect = on_connect
    client.message_callback_add(
        "controller/discover/switch/#", on_discover_switch)
    client.message_callback_add(
        "controller/discover/sensor/#", on_discover_sensor)
    client.message_callback_add(
        "controller/discover/cover/#", on_discover_blinds)
    client.connect(HOST)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()
