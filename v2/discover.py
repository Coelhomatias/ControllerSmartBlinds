import datetime as dt
import json
import multiprocessing as mp
import time
from multiprocessing import Process, Value

import apscheduler as aps
import holidays
import joblib
import numpy as np
import paho.mqtt.client as mqtt
import pandas as pd
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from creme import metrics

import device
from cover_classes import Blinds, Metrics, Sensor, Switch
from device import Device
from mqttComponent import MQTTComponent

FILE_PATH = "saved_devices.txt"
HOST = "192.168.0.2"
USER = "Coelhomatias"
PASSWORD = "lf171297"
NUMBER_OF_SENSORS = 2
NUMBER_OF_METRICS = 2
TRAIN_EVERY = 1  # minutes
SAVE_TIME_H = 4  # At what hour of the day
SAVE_TIME_M = 30  # At what minute
STOP_PRED_INTERVAL = 30  # minutes
MAX_DEVICES = mp.cpu_count() + 2
number_of_devices = 0

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Discover connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("controller/discover/#", 1)
    try:
        for dic in nodes:
            nodes[dic]["mqtt"].run()
            nodes[dic]["train_job"].resume()
            nodes[dic]["save_job"].resume()
    except:
        pass

def on_disconnect(client, userdata, rc):
    print("Discover disconnected with result code " + str(rc))
    for dic in nodes:
        nodes[dic]["mqtt"].stop()
        nodes[dic]["train_job"].pause()
        nodes[dic]["save_job"].pause()


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
        try:
            # Add Sensor to Device
            nodes[device_id]["device"].add_Sensor(Sensor(
                parsed["name"], parsed["unique_id"], parsed["state_topic"], parsed["unit_of_measurement"]))
            # Handle MQTT subscribe and callbacks
            nodes[device_id]["mqtt"].subscribe_to_topic(
                parsed["state_topic"], 1)
            nodes[device_id]["mqtt"].add_message_callback(
                parsed["state_topic"], nodes[device_id]["device"].on_sensor_state_change)
        except:
            if 'mae' in parsed["state_topic"]:
                nodes[device_id]["device"].add_Metrics(Metrics(
                    parsed["name"], parsed["unique_id"], parsed["state_topic"], metrics.MAE()))
            elif 'rmse' in parsed["state_topic"]:
                nodes[device_id]["device"].add_Metrics(Metrics(
                    parsed["name"], parsed["unique_id"], parsed["state_topic"], metrics.RMSE()))
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
            nodes[availability[msg.topic]]["save_job"].resume()
        else:
            nodes[availability[msg.topic]]["mqtt"].stop()
            nodes[availability[msg.topic]]["train_job"].pause()
            nodes[availability[msg.topic]]["save_job"].pause()


def create_device(dictionary, device_id):
    global number_of_devices
    node = {
        "device": Device(dictionary["device"]["name"] + '_' + "Device", device_id, dictionary["availability_topic"], NUMBER_OF_SENSORS, NUMBER_OF_METRICS),
        "mqtt": MQTTComponent(device_id, credentials["mqtt_host"], credentials["mqtt_user"], credentials["mqtt_passwd"], name=dictionary["device"]["name"] + '_' + "MQQTComponent", alt_client=client)
    }
    try:
        time = dt.datetime.now()
        data = joblib.load("Models\\" + device_id + '.gz')
        print("Took", dt.datetime.now() - time, "seconds to load model")
        node["device"].set_model(data["model"])
        node["device"].set_date_of_birth(data["date_of_birth"])
        for metric in data["metrics"]:
            node["device"].add_Metrics(data["metrics"][metric])
        print("Loading existing model for device:", device_id)
    except:
        pass
    nodes[device_id] = node
    nodes[device_id]["mqtt"].run()
    availability[dictionary["availability_topic"]] = device_id
    number_of_devices += 1
    print("Added new device to nodes with identifier:", device_id)


def check_if_finished(device_id):
    if nodes[device_id]["device"].is_full() and not "train_job" in nodes[device_id] and not "save_job" in nodes[device_id]:
        print("Device Finished. Starting Jobs")
        train_job = scheduler.add_job(func=train_device, args=(
            device_id, ), executor='default', trigger='cron', minute=('*/' + str(TRAIN_EVERY)))
        save_job = scheduler.add_job(func=save_device, args=(
            nodes[device_id]["device"], ), executor='processpool', misfire_grace_time=5, trigger='cron', minute="*")
        nodes[device_id]["train_job"] = train_job
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
    last_pred = nodes[device_id]["device"].get_last_pred()
    y_pred = nodes[device_id]["device"].predict(X)
    
    """ if last_pred != y and last_pred != None and nodes[device_id]["device"].get_able_to_predict():  # The user changed position
        # Stop predicting for 30 minutes
        print("Wrong prediction, waiting 30 minutes...")
        nodes[device_id]["device"].set_able_to_predict(False)
        scheduler.add_job(func=nodes[device_id]["device"].set_able_to_predict, args=(
            True,), trigger='interval', minutes=STOP_PRED_INTERVAL)

    if nodes[device_id]["device"].get_able_to_predict() and nodes[device_id]["device"].get_state_Switch() == "ON":
        print("Sending prediction to:", device_id)
        nodes[device_id]["mqtt"].publish_to_topic(
            nodes[device_id]["device"]._blinds.get_command_topic(), y_pred, 1)
        nodes[device_id]["device"].set_last_pred(y_pred) """

    nodes[device_id]["device"].partial_fit(X, [y])
    nodes[device_id]["device"].update_Metrics(y, y_pred, nodes[device_id]["mqtt"])
    nodes[device_id]["save_job"].modify(
        args=(nodes[device_id]["device"], ))
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
    return X.to_numpy(), y


def save_device(device):
    device_id = device.get_id()
    data = {
        "model": device.get_model(),
        "date_of_birth": device.get_date_of_birth(),
        "metrics": device.get_Metrics()
    }
    print("Inside save_device Process. Saving device")
    time = dt.datetime.now()
    joblib.dump(
        data, "Models\\" + device_id + '.gz', compress=('gzip', 3))
    print("Took", dt.datetime.now() - time, "seconds to save model")


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
    client.on_disconnect = on_disconnect
    client.message_callback_add(
        "controller/discover/switch/#", on_discover_switch)
    client.message_callback_add(
        "controller/discover/sensor/#", on_discover_sensor)
    client.message_callback_add(
        "controller/discover/cover/#", on_discover_blinds)
    client.connect(HOST)
    client.loop_forever()
