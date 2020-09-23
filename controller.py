from Device import Device
from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch
from skmultiflow.meta import AdaptiveRandomForestRegressor
import paho.mqtt.client as mqtt
import json


class Controller:

    def __init__(self, name, identifier, availability_topic, mqtt_host, mqtt_user, mqtt_pass, model=AdaptiveRandomForestRegressor(random_state=43, n_estimators=100, grace_period=50, max_features=11, leaf_prediction='mean', split_confidence=0.09, lambda_value=10)):
        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
        self._model = model
        self._device = Device(name, identifier, availability_topic)
        self._client = mqtt.Client()
        self._client.username_pw_set(username=mqtt_user, password=mqtt_pass)
        self._client.on_connect = self.on_connect
        self._client.connect(mqtt_host)
        self._client.loop_start()

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

    def subscribe_to_topic(self, topic, qos):
        self._client.subscribe(topic, qos)

    def add_component(self, component):
        if type(component) is Blinds:
            self._device.set_Blinds(component)
            self.subscribe_to_topic(component.get_position_topic(), 1)
            self._client.message_callback_add(
                component.get_position_topic(), self.on_position_change)
        elif type(component) is Sensor:
            self._device.add_Sensor(component)
            self.subscribe_to_topic(component.get_state_topic(), 1)
            self._client.message_callback_add(
                component.get_state_topic(), self.on_sensor_state_change)
        elif type(component) is Switch:
            self._device.set_Switch(component)
            self.subscribe_to_topic(component.get_state_topic(), 1)
            self._client.message_callback_add(
                component.get_state_topic(), self.on_switch_state_change)

    def on_connect(self, client, userdata, flags, rc):
        print(self._name + " connected with result code: " + str(rc))

    def on_position_change(self, client, userdata, msg):
        print("Received Blind Position Change from topic: " + msg.topic)

    def on_sensor_state_change(self, client, userdata, msg):
        print("Received Sensor State Change from topic: " + msg.topic)

    def on_switch_state_change(self, client, userdata, msg):
        print("Received Switch State Change from topic: " + msg.topic)
