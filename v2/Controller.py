from MQTTComponent import MQTTComponent
from skmultiflow.meta import AdaptiveRandomForestRegressor
from resettabletimer import ResettableTimer
import datetime as dt
import time
import copy
import joblib

class Controller():

    def __init__(
            self, name, identifier, device, timeout=350, learning_time=dt.timedelta(days=7),
            model=AdaptiveRandomForestRegressor(random_state=43, n_estimators=100, grace_period=50, max_features=11, leaf_prediction='mean', split_confidence=0.09, lambda_value=10)):

        self._name = name
        self._identifier = identifier
        self._device = device
        self._timeout = timeout #In seconds
        self._date_of_birth = dt.datetime.now()
        self._learning_time = learning_time
        self._model = model
        self._mqtt = None
        self._timer = None
        #Flags...
        self._is_active = True

    def get_name(self):
        return self._name

    def get_id(self):
        return self._identifier

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

    def set_MQTTComponent(self, mqtt_host, mqtt_user, mqtt_passwd):
        self._mqtt = MQTTComponent(
            mqtt_host, mqtt_user, mqtt_passwd, self._name + "_mqttComponent")
        self._mqtt.run()
        # Subscribe to and add Callbacks to switch/state
        self._mqtt.subscribe_to_topic(
            self._device._switch.get_state_topic(), 1)
        self._mqtt.add_message_callback(
            self._device._switch.get_state_topic(), self.on_switch_state_change)
        # Subscribe to and add Callbacks to cover/state
        self._mqtt.subscribe_to_topic(
            self._device._blinds.get_position_topic(), 1)
        self._mqtt.add_message_callback(
            self._device._blinds.get_position_topic(), self.on_position_change)
        # Subscribe to and add Callbacks to sensor/state
        for sensor in self._device._sensors:
            self._mqtt.subscribe_to_topic(sensor, 1)
            self._mqtt.add_message_callback(
                sensor, self.on_sensor_state_change)
        #Set the Timer
        self._timer = ResettableTimer(self._timeout, self.set_availability)
        self._timer.reset()

    def stop_MQTTComponent(self):
        self._mqtt.stop()
        del self._mqtt
        self._timer.cancel()
        del self._timer
    

    def on_position_change(self, client, userdata, msg):
        print("Received Blind Position Change from topic: " +
              msg.topic + ' --> ' + msg.payload.decode())
        self._device.set_position_Blinds(msg.payload.decode())
        self._timer.reset()
        self._is_active = True

    def on_sensor_state_change(self, client, userdata, msg):
        print("Received Sensor State Change from topic: " +
              msg.topic + ' --> ' + msg.payload.decode())
        self._device.set_value_Sensor(msg.topic, msg.payload.decode())
        self._timer.reset()
        self._is_active = True

    def on_switch_state_change(self, client, userdata, msg):
        print("Received Switch State Change from topic: " +
              msg.topic + ' --> ' + msg.payload.decode())
        if (dt.datetime.now() >= self._date_of_birth + self._learning_time):
            self._device.set_state_Switch(msg.payload.decode())
        elif msg.payload.decode() == "ON":
            self._mqtt.publish_to_topic(
                topic=self._device._switch.get_command_topic(), payload="OFF", qos=1)
        self._timer.reset()
        self._is_active = True
    
    def set_availability(self):
        self._is_active = False


def execution(device, credentials, run):
    control = Controller(device.get_name() + "_controller", device.get_id(), device)
    control.set_MQTTComponent(credentials["mqtt_host"], credentials["mqtt_user"], credentials["mqtt_passwd"])
    #time.sleep(10)
    #control.stop_MQTTComponent()
    #t = dt.datetime.now()
    #joblib.dump(control, "temp.txt")
    #print("Time to write:", dt.datetime.now() - t)
    #control.set_MQTTComponent(credentials["mqtt_host"], credentials["mqtt_user"], credentials["mqtt_passwd"])
    while True:
        if run.value and control._is_active:
            print("Inside Process motherfucker!!")
            time.sleep(1)
        else:
            print("Process paused, waiting for node!!")
            time.sleep(1)
