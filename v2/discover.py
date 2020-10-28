import datetime as dt
import json
import multiprocessing as mp
import time
import threading
import atexit
from multiprocessing import Process, Value

import logging
import colorstreamhandler
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
import cover_classes
import mqttComponent
from cover_classes import Blinds, Metrics, Sensor, Switch
from device import Device
from mqttComponent import MQTTComponent


############################# USER CONFIG #############################
HOST = "192.168.0.2"
PORT = 12183  # PORT = 1883
USER = ''  # USER = "Coelhomatias"
PASSWORD = ''  # PASSWORD = "lf171297"
#FILEPATH = "C:\\Users\\Leandro Filipe\\Documents\\FCT\\5º ano\\Tese\\ControllerSmartBlinds\\Models\\"
FILEPATH = "/home/pi/ControllerSmartBlinds/Models/"
NUMBER_OF_SENSORS = 4
NUMBER_OF_METRICS = 2
TRAINING_TIME = dt.timedelta(minutes=5)
ALLOWED_ERROR = 2
TRAIN_EVERY = 1  # minutes
SAVE_TIME_H = 4  # At what hour of the day
SAVE_TIME_M = 30  # At what minute
STOP_PRED_INTERVAL = 5  # minutes
MAX_DEVICES = mp.cpu_count() + 2
########################## END OF USER CONFIG #########################

number_of_devices = 0


def on_connect(client, userdata, flags, rc):
    logger.log('debug', "Discover connected with result code " + str(rc))

    client.subscribe("controller/discover/#", 1)
    try:
        for dic in nodes:
            nodes[dic]["mqtt"].run()
            nodes[dic]["train_job"].resume()
            nodes[dic]["save_job"].resume()
    except:
        pass


def on_disconnect(client, userdata, rc):
    logger.log('debug', "Discover disconnected with result code " + str(rc))
    for dic in nodes:
        nodes[dic]["mqtt"].stop()
        nodes[dic]["train_job"].pause()
        nodes[dic]["save_job"].pause()


def on_discover_switch(client, userdata, msg):
    if number_of_devices < MAX_DEVICES:
        parsed = json.loads(msg.payload.decode())
        logger.log('info', "Just discovered switch: " + parsed["unique_id"])
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
        logger.log('info', "Just discovered sensor: " + parsed["unique_id"])
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
                    parsed["name"], parsed["unique_id"], parsed["state_topic"], metrics.Rolling(metrics.MAE(), int(10080/TRAIN_EVERY))))
            elif 'rmse' in parsed["state_topic"]:
                nodes[device_id]["device"].add_Metrics(Metrics(
                    parsed["name"], parsed["unique_id"], parsed["state_topic"], metrics.Rolling(metrics.RMSE(), int(10080/TRAIN_EVERY))))
        # Check if Device as all components
        check_if_finished(device_id)


def on_discover_blinds(client, userdata, msg):
    if number_of_devices < MAX_DEVICES:
        parsed = json.loads(msg.payload.decode())
        logger.log('info', "Just discovered blinds: " + parsed["unique_id"])
        device_id = (parsed["device"]["name"] + "_" +
                     parsed["device"]["identifiers"])
        if not device_id in nodes:
            create_device(parsed, device_id)
        # Add Blinds to Device
        nodes[device_id]["device"].set_Blinds(Blinds(
            parsed["name"], parsed["unique_id"], parsed["position_topic"], parsed["set_position_topic"]))
        # Handle MQTT subscribe and callbacks
        nodes[device_id]["mqtt"].subscribe_to_topic(
            parsed["position_topic"], 1)
        nodes[device_id]["mqtt"].add_message_callback(
            parsed["position_topic"], nodes[device_id]["device"].on_position_change)
        # Check if Device as all components
        check_if_finished(device_id)


def on_availability(client, userdata, msg):
    if msg.topic in availability:
        if msg.payload.decode() == "online":
            logger.log('info', availability[msg.topic] + " are now online")
            nodes[availability[msg.topic]]["mqtt"].run()
            nodes[availability[msg.topic]]["train_job"].resume()
            nodes[availability[msg.topic]]["save_job"].resume()
        else:
            logger.log('info', availability[msg.topic] + " are now offline")
            nodes[availability[msg.topic]]["mqtt"].stop()
            nodes[availability[msg.topic]]["train_job"].pause()
            nodes[availability[msg.topic]]["save_job"].pause()


def create_device(dictionary, device_id):
    global number_of_devices
    try:
        time = dt.datetime.now()
        data = joblib.load(FILEPATH + device_id)
        logger.log('info', "Loaded existing device: " + device_id)
        logger.log('debug', "Took " + str(dt.datetime.now() - time) +
                     " seconds to load " + device_id)
        node = {"device": data}
    except:
        logger.log('info', "Creating new device: " + device_id)
        node = {"device": Device(dictionary["device"]["name"] + '_' + "Device", device_id,
                                 dictionary["availability_topic"], NUMBER_OF_SENSORS, NUMBER_OF_METRICS, logger=create_logger(device_id), learning_time=TRAINING_TIME)}
    node["mqtt"] = MQTTComponent(device_id, credentials["mqtt_host"], credentials["mqtt_user"], credentials["mqtt_passwd"],
                                 credentials["mqtt_port"], logger=create_logger(device_id + "_mqtt"), name=dictionary["device"]["name"] + '_' + "MQQTComponent", alt_client=client)
    nodes[device_id] = node
    nodes[device_id]["mqtt"].run()
    availability[dictionary["availability_topic"]] = device_id
    number_of_devices += 1
    logger.log('info', "Added device to nodes with identifier: " + device_id)


def check_if_finished(device_id):
    if nodes[device_id]["device"].is_full() and not "train_job" in nodes[device_id] and not "save_job" in nodes[device_id]:
        logger.log('info', device_id + " Finished")
        logger.log('info', "Adding jobs to node " + device_id)
        train_job = scheduler.add_job(func=train_device, args=(
            device_id, ), executor='default', trigger='cron', minute=('*/' + str(TRAIN_EVERY)))
        save_job = scheduler.add_job(func=save_device, args=(
            nodes[device_id]["device"], ), executor='processpool', misfire_grace_time=30, trigger='cron', minute="*/5")  # Must change trigger
        nodes[device_id]["train_job"] = train_job
        nodes[device_id]["save_job"] = save_job
        logger.log('info', "Starting jobs for " + device_id)
        # Availability section
        client.subscribe(
            nodes[device_id]["device"].get_availability_topic(), 1)
        client.message_callback_add(
            nodes[device_id]["device"].get_availability_topic(), on_availability)


def train_device(device_id):
    nodes[device_id]["device"].log_message(
        'info', "Getting example for training")
    with lock:
        X, y = prepare_example(device_id)
        last_example = nodes[device_id]["device"].get_last_example()
        last_pred = nodes[device_id]["device"].get_last_pred()
        y_pred = nodes[device_id]["device"].predict(X)
        nodes[device_id]["device"].log_message(
            'debug', "Predicted next value for position: " + str(y_pred))
        nodes[device_id]["device"].set_last_pred(y_pred)
        nodes[device_id]["device"].set_last_example(X)

        if nodes[device_id]["device"].get_state_Switch() == "ON" and nodes[device_id]["device"].get_able_to_predict():
            # The user changed position
            if last_pred not in list(range(y - ALLOWED_ERROR, y + ALLOWED_ERROR + 1)):
                # Stop predicting for 30 minutes
                nodes[device_id]["device"].log_message(
                    'warning', "Wrong Prediction!")
                nodes[device_id]["device"].log_message(
                    'info', "Waiting " + str(STOP_PRED_INTERVAL) + " minutes to next prediction")
                nodes[device_id]["device"].set_able_to_predict(False)
                scheduler.add_job(func=nodes[device_id]["device"].set_able_to_predict, args=(
                    True,), trigger='interval', minutes=STOP_PRED_INTERVAL, seconds=1)
                # nodes[device_id]["device"].set_last_pred(None)

            if nodes[device_id]["device"].get_able_to_predict():
                nodes[device_id]["device"].log_message(
                    'info', "Sending prediction to device")
                nodes[device_id]["mqtt"].publish_to_topic(
                    nodes[device_id]["device"]._blinds.get_command_topic(), y_pred, 1)
        
        if last_example.size != 0 and last_pred != None:
            nodes[device_id]["device"].log_message(
                'info', "Training device's model")
            nodes[device_id]["device"].partial_fit(last_example, [y])
            nodes[device_id]["device"].update_Metrics(
                y, last_pred, nodes[device_id]["mqtt"])
            nodes[device_id]["save_job"].modify(
                args=(nodes[device_id]["device"], ))


def prepare_example(device_id):
    X, y = nodes[device_id]["device"].get_example()
    X = pd.DataFrame([X])
    X['time'] = dt.datetime.now()
    X['quarter'] = X.time.dt.quarter
    X['month'] = X.time.dt.month
    X['weekofyear'] = X.time.dt.isocalendar().week
    X['dayofmonth'] = X.time.dt.day
    X['dayofyear'] = X.time.dt.dayofyear
    X['dayofweek'] = X.time.dt.dayofweek
    X['hour'] = X.time.dt.hour
    X['minute'] = X.time.dt.minute
    X['holiday'] = X.time.dt.date.isin(pt_holidays).astype(int)
    X['lights'] = [1 if (row[1] > row[3] or (
        row[1] > 0 and y == 0)) else 0 for row in X.to_numpy()]
    X = X.drop(columns='time')
    # print(X.head())
    return X.to_numpy(), y


def save_device(device):
    device_id = device.get_id()
    # data = {
    #     "model": device.get_model(),
    #     "date_of_birth": device.get_date_of_birth(),
    #     "metrics": device.get_Metrics()
    # }
    device.log_message('info', "Saving device")
    time = dt.datetime.now()
    joblib.dump(
        device, FILEPATH + device_id)
    device.log_message(
        'debug', "Took " + str(dt.datetime.now() - time) + " seconds to save model")


def create_logger(name):
    return colorstreamhandler.ColorLogger(name)

def OnExitApp(user):
    for node in nodes:
        nodes[node]["mqtt"].stop()
    scheduler.remove_all_jobs()
    scheduler.shutdown()
    logger.log('info', user + " Exiting gracefully of the Adaptive Controller")


if __name__ == "__main__":

    print("Starting the Adaptive Controller...")

    nodes = dict()
    availability = dict()
    credentials = {
        "mqtt_host": HOST,
        "mqtt_user": USER,
        "mqtt_passwd": PASSWORD,
        "mqtt_port": PORT
    }
    executors = {
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(mp.cpu_count() + 2)
    }
    pt_holidays = holidays.PT()
    lock = threading.Lock()

    logger = create_logger('adaptive_controller')
    atexit.register(OnExitApp, user='Leandro Filipe')

    try:
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
        client.connect(HOST, PORT)
        client.loop_forever()
    except KeyboardInterrupt:
        pass
