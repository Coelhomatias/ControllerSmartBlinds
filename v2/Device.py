from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch
from skmultiflow.meta import AdaptiveRandomForestRegressor
from multiprocessing import Value
import datetime as dt


class Device:

    def __init__(self, name, identifier, availability_topic, number_of_sensors, timeout=350, learning_time=dt.timedelta(days=7),
            model=AdaptiveRandomForestRegressor(random_state=43, n_estimators=100, grace_period=50, max_features=11, leaf_prediction='mean', split_confidence=0.09, lambda_value=10)):
        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
        self._timeout = timeout #In seconds
        self._date_of_birth = dt.datetime.now()
        self._learning_time = learning_time
        self._model = model
        self._sensors = {}
        self._switch = None
        self._blinds = None
        self._number_of_sensors = number_of_sensors

    def get_name(self):
        return self._name

    def get_id(self):
        return self._identifier

    def get_availability_topic(self):
        return self._availability_topic
    
    def get_date_of_birth(self):
        return self._date_of_birth
    
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

    def set_Blinds(self, blinds):
        self._blinds = blinds

    def set_position_Blinds(self, position):
        self._blinds.set_position(position)

    def get_position_Blinds(self):
        return self._blinds.get_position()

    def add_Sensor(self, sensor):
        self._sensors[sensor.get_state_topic()] = sensor

    def set_value_Sensor(self, state_topic, value):
        self._sensors[state_topic].set_value(value)

    def get_value_Sensor(self, state_topic):
        return self._sensors[state_topic].get_value()

    def get_value_all_Sensor(self):
        values = {}
        for sensor in self._sensors:
            values[sensor.split("/")[-2]] = self._sensors[sensor].get_value()
        return values

    def set_Switch(self, switch):
        self._switch = switch

    def get_state_Switch(self):
        return self._switch.get_state()

    def set_state_Switch(self, state):
        self._switch.set_state(state)

    def get_example(self):
        y = self.get_position_Blinds()
        X = self.get_value_all_Sensor()
        return X, y

    def is_full(self):
        if self._blinds and self._switch and len(self._sensors) == self._number_of_sensors:
            return True
        return False
    
    def on_position_change(self, client, userdata, msg):
        print("Received Blind Position Change from topic: " +
              msg.topic + ' --> ' + msg.payload.decode())
        self.set_position_Blinds(int(msg.payload.decode()))

    def on_sensor_state_change(self, client, userdata, msg):
        print("Received Sensor State Change from topic: " +
              msg.topic + ' --> ' + msg.payload.decode())
        self.set_value_Sensor(msg.topic, float(msg.payload.decode()))

    def on_switch_state_change(self, client, userdata, msg):
        print("Received Switch State Change from topic: " +
              msg.topic + ' --> ' + msg.payload.decode())
        if (dt.datetime.now() >= self._date_of_birth + self._learning_time):
            self.set_state_Switch(msg.payload.decode())
        elif msg.payload.decode() == "ON":
            userdata['alt_client'].publish(
                topic=self._switch.get_command_topic(), payload="OFF", qos=1)