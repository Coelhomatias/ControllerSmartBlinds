import paho.mqtt.client as mqtt
import json
import time
import joblib
import pandas as pd
import numpy as np
import holidays
import datetime as dt
# Custom Classes
from mqttComponent import MQTTComponent
from cover_classes import Blinds, Sensor, Switch
import device
from device import Device
# Multiprocessing
import multiprocessing as mp
from multiprocessing import Process, Value
# Scheduler
import apscheduler as aps
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

FILE_PATH = "saved_devices.txt"
HOST = "192.168.0.2"
USER = "Coelhomatias"
PASSWORD = "lf171297"
NUMBER_OF_SENSORS = 2
MAX_DEVICES = mp.cpu_count() + 2
number_of_devices = 0

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Discover connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("controller/discover/#", 1)


def on_discover_switch(client, userdata, msg):
    if number_of_devices < MAX_DEVICES:
        parsed = json.loads(msg.payload.decode())
        print("Just discovered switch: " + parsed["unique_id"])
        device_id = (parsed["device"]["name"] + "_" +
                     parsed["device"]["identifiers"])
        if not device_id in nodes:
            create_device(parsed, device_id)

        # Add Switch to Device
        nodes[device_id]["device"].set_Switch(Switch(
            parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["command_topic"]))
        # Handle MQTT subscribe and callbacks
        nodes[device_id]["mqtt"].subscribe_to_topic(parsed["state_topic"], 1)
        nodes[device_id]["mqtt"].add_message_callback(
            parsed["state_topic"], nodes[device_id]["device"].on_switch_state_change)
        # Check if Device as all components
        check_if_finished(device_id)


def on_discover_sensor(client, userdata, msg):
    if number_of_devices < MAX_DEVICES:
        parsed = json.loads(msg.payload.decode())
        print("Just discovered sensor: " + parsed["unique_id"])
        device_id = (parsed["device"]["name"] + "_" +
                     parsed["device"]["identifiers"])
        if not device_id in nodes:
            create_device(parsed, device_id)

        # Add Sensor to Device
        nodes[device_id]["device"].add_Sensor(Sensor(
            parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["unit_of_measurement"]))
        # Handle MQTT subscribe and callbacks
        nodes[device_id]["mqtt"].subscribe_to_topic(parsed["state_topic"], 1)
        nodes[device_id]["mqtt"].add_message_callback(
            parsed["state_topic"], nodes[device_id]["device"].on_sensor_state_change)
        # Check if Device as all components
        check_if_finished(device_id)


def on_discover_blinds(client, userdata, msg):
    if number_of_devices < MAX_DEVICES:
        parsed = json.loads(msg.payload.decode())
        print("Just discovered blinds: " + parsed["unique_id"])
        device_id = (parsed["device"]["name"] + "_" +
                     parsed["device"]["identifiers"])
        if not device_id in nodes:
            create_device(parsed, device_id)

        # Add Blinds to Device
        nodes[device_id]["device"].set_Blinds(Blinds(
            parsed["name"], parsed["unique_id"], parsed["position_topic"], parsed["command_topic"]))
        # Handle MQTT subscribe and callbacks
        nodes[device_id]["mqtt"].subscribe_to_topic(
            parsed["position_topic"], 1)
        nodes[device_id]["mqtt"].add_message_callback(
            parsed["position_topic"], nodes[device_id]["device"].on_position_change)
        # Check if Device as all components
        check_if_finished(device_id)


def on_availability(client, userdata, msg):
    print("Availability message from topic,", msg.topic,
          "with payload:", msg.payload.decode())
    if msg.topic in availability:
        if msg.payload.decode() == "online":
            nodes[availability[msg.topic]]["mqtt"].run()
            nodes[availability[msg.topic]]["train_job"].resume()
            nodes[availability[msg.topic]]["update_job"].resume()
            nodes[availability[msg.topic]]["save_job"].resume()
        else:
            nodes[availability[msg.topic]]["mqtt"].stop()
            nodes[availability[msg.topic]]["train_job"].pause()
            nodes[availability[msg.topic]]["update_job"].pause()
            nodes[availability[msg.topic]]["save_job"].pause()


def create_device(dictionary, device_id):
    global number_of_devices
    node = {
        "device": Device(dictionary["device"]["name"] + '_' + "Device", device_id, dictionary["availability_topic"], NUMBER_OF_SENSORS),
        "mqtt": MQTTComponent(device_id, credentials["mqtt_host"], credentials["mqtt_user"], credentials["mqtt_passwd"], name=dictionary["device"]["name"] + '_' + "MQQTComponent", alt_client=client)
    }
    nodes[device_id] = node
    nodes[device_id]["mqtt"].run()
    availability[dictionary["availability_topic"]] = device_id
    number_of_devices += 1
    print("Added new device to nodes with identifier:", device_id)


def check_if_finished(device_id):
    if nodes[device_id]["device"].is_full() and not "train_job" in nodes[device_id]:
        print("Device Finished. Starting Jobs")
        train_job = scheduler.add_job(func=train_device, args=(
            device_id, ), executor='default', trigger='cron', minute='*/5')
        update_job = scheduler.add_job(func=update_device, args=(
            device_id,), executor='default', trigger='cron', minute="*", second=58)
        save_job = scheduler.add_job(func=save_device, args=(
            device_id,), executor='processpool', misfire_grace_time=5, trigger='cron', minute="*")
        nodes[device_id]["train_job"] = train_job
        nodes[device_id]["update_job"] = update_job
        nodes[device_id]["save_job"] = save_job
        print("Added new jobs to node. The processes were started")
        # Availability section
        client.subscribe(
            nodes[device_id]["device"].get_availability_topic(), 1)
        client.message_callback_add(
            nodes[device_id]["device"].get_availability_topic(), on_availability)


def train_device(device_id):
    print("Getting example...")
    X, y = prepare_example(device_id)
    nodes[device_id]["device"].partial_fit(X, y)
    print("Training " + device_id + "'s model")

def prepare_example(device_id):
    X, y = nodes[device_id]["device"].get_example()
    X = pd.DataFrame([X])
    X['time'] = dt.datetime.now()
    X['quarter'] = X.time.dt.quarter
    X['month'] = X.time.dt.month
    X['weekofyear'] = X.time.dt.weekofyear
    X['dayofmonth'] = X.time.dt.day
    X['dayofyear'] = X.time.dt.dayofyear
    X['dayofweek'] = X.time.dt.dayofweek
    X['hour'] = X.time.dt.hour
    X['minute'] = X.time.dt.minute
    X['holiday'] = X.time.dt.date.isin(pt_holidays).astype(int)
    #X['lights'] = [1 if (row[2] > row[3] or (row[2] > 0 and row[1] == 0)) else 0 for row in X.to_numpy()]
    X = X.drop(columns='time')
    return X.to_numpy(), [y]


def update_device(device_id):
    print("Updating job!!")
    nodes[device_id]["save_job"].modify(
        args=(nodes[device_id]["device"], ))


def save_device(device):
    saved = False
    device_id = device.get_id()
    print("Inside save_device Process. Saving device")

    try:
        with open(FILE_PATH, "rt") as f:
            for dev_id in f:
                if device_id in dev_id:
                    saved = True
    except:
        pass
    time = dt.datetime.now()
    joblib.dump(
        device, "Devices\\" + device_id)
    print("Took", dt.datetime.now() - time, "seconds to save Device")
    if not saved:
        with open(FILE_PATH, "at") as f:
            f.write(device_id + '\n')
            f.flush()
    print("Inside save_device Process. Finished saving Device")


if __name__ == "__main__":

    nodes = dict()
    availability = dict()
    credentials = {
        "mqtt_host": HOST,
        "mqtt_user": USER,
        "mqtt_passwd": PASSWORD
    }
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(mp.cpu_count() + 2)
    }
    pt_holidays = holidays.PT()

    scheduler = BackgroundScheduler(executors=executors)
    scheduler.start()

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
