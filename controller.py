from Device import Device
from MQTTComponent import MQTTComponent
from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch
from skmultiflow.meta import AdaptiveRandomForestRegressor
from multiprocessing import Process
import time
import datetime as dt
import json


class Controller():

    def __init__(self, name, identifier, availability_topic, mqtt_host, mqtt_user, mqtt_passwd, learning_time=dt.timedelta(days=7), model=AdaptiveRandomForestRegressor(random_state=43, n_estimators=100, grace_period=50, max_features=11, leaf_prediction='mean', split_confidence=0.09, lambda_value=10)): 

        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
        self._learning_time = learning_time
        self._model = model
        self._device = Device(name, identifier, availability_topic)
        self._mqtt = MQTTComponent(mqtt_host, mqtt_user, mqtt_passwd, name + "_mqttComponent")
        self._mqtt.run()
        self._process = Process(target=self.run)
        self._process.daemon = True
        self._process.start()
        self._mqtt_running = False
        self._is_running = True
        self._waiting_for_confirm = False

    def get_name(self):
        return self._name

    def get_id(self):
        return self._identifier

    def get_availability_topic(self):
        return self._availability_topic

    def set_model(self, model):
        self._model = model

    def get_model(self):
        return self._model

    def predict(self, X):
        return self._model.predict(X)

    def fit(self, X, y):
        self._model.fit(X, y)

    def partial_fit(self, X, y):
        self._model.partial_fit(X, y)

    def add_component(self, component):
        if type(component) is Blinds:
            print("Adding Blinds")
            self._device.set_Blinds(component)
            self._mqtt.subscribe_to_topic(component.get_position_topic(), 1)
            self._mqtt.add_message_callback(
                component.get_position_topic(), self.on_position_change)
        elif type(component) is Sensor:
            print("Adding Sensor")
            self._device.add_Sensor(component)
            self._mqtt.subscribe_to_topic(component.get_state_topic(), 1)
            self._mqtt.add_message_callback(
                component.get_state_topic(), self.on_sensor_state_change)
        elif type(component) is Switch:
            print("Adding Switch")
            self._device.set_Switch(component)
            self._mqtt.subscribe_to_topic(component.get_state_topic(), 1)
            self._mqtt.add_message_callback(
                component.get_state_topic(), self.on_switch_state_change)

    def on_position_change(self, client, userdata, msg):
        print("Received Blind Position Change from topic: " + msg.topic + ' --> ' + msg.payload.decode())
        self._device.set_position_Blinds(msg.payload.decode())

    def on_sensor_state_change(self, client, userdata, msg):
        print("Received Sensor State Change from topic: " + msg.topic + ' --> ' + msg.payload.decode())
        self._device.set_value_Sensor_with_topic(msg.topic, msg.payload.decode())

    def on_switch_state_change(self, client, userdata, msg):
        print("Received Switch State Change from topic: " + msg.topic + ' --> ' + msg.payload.decode())
        if (dt.datetime.now() >= self._device.get_date_of_birth() + self._learning_time):
            self._device.set_state_Switch(msg.payload.decode())
        elif msg.payload.decode() == "ON":
            self._mqtt.publish_to_topic(topic=self._device._switch.get_command_topic(), payload="OFF", qos=1)
            pass
    
    def is_mqtt_running(self):
        return self._mqtt_running
 
    def run(self):
        while True:
            print("im in run   " + str(dt.datetime.now()))
            time.sleep(5)
        return

        
