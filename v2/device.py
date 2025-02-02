from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch
from skmultiflow.meta import AdaptiveRandomForestRegressor
from creme import linear_model
from creme import compose
from creme import preprocessing
from multiprocessing import Value
import datetime as dt
import numpy as np


class Device:

    def __init__(self, name, identifier, availability_topic, number_of_sensors, number_of_metrics, logger, model, learning_time=dt.timedelta(days=7)):
        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
        self._date_of_birth = dt.datetime.now()
        self._learning_time = learning_time
        self._sensors = {}
        self._metrics = {}
        self._switch = None
        self._blinds = None
        self._number_of_sensors = number_of_sensors
        self._number_of_metrics = number_of_metrics
        self._logger = logger
        #self._last_true = 100
        self._last_example = np.array([])
        self._last_pred = None
        self._able_to_predict = True
        
        if model == 1:
            self.log_message('info', 'Using AdaptiveRandomForestRegressor model')
            self._model = AdaptiveRandomForestRegressor(random_state=43, n_estimators=100, grace_period=50, max_features=11, leaf_prediction='mean', split_confidence=0.09, lambda_value=10)
        elif model == 2:
            self.log_message('info', 'Using PARegressor model')
            self._model = preprocessing.StandardScaler() | compose.Discard('lights') | linear_model.PARegressor(C=0.05, mode=1, eps=0.1)

    def get_name(self):
        return self._name

    def get_id(self):
        return self._identifier

    def get_availability_topic(self):
        return self._availability_topic

    def get_date_of_birth(self):
        return self._date_of_birth

    def set_date_of_birth(self, date):
        self._date_of_birth = date

    def set_last_pred(self, pred):
        self._last_pred = pred

    def get_last_pred(self):
        return self._last_pred
    
    def set_last_example(self, example):
        self._last_example = example

    def get_last_example(self):
        return self._last_example

    def set_able_to_predict(self, val):
        self._able_to_predict = val

    def get_able_to_predict(self):
        return self._able_to_predict

    def set_model(self, model):
        self._model = model

    def get_model(self):
        return self._model

    def predict(self, X):
        if hasattr(self._model, 'predict'):
            prediction = max(min(round(self._model.predict(X.to_numpy())[0]), 100), 0)
        elif hasattr(self._model, 'predict_one'):
            prediction = max(min(round(self._model.predict_one(X.to_dict(orient='records')[0])), 100), 0)
        return prediction

    def partial_fit(self, X, y):
        if hasattr(self._model, 'partial_fit'):
            #print("hellooooo from ARFR")
            self._model.partial_fit(X.to_numpy(), [y])
        elif hasattr(self._model, 'fit_one'):
            #print("hellooooo from PAR")
            self._model.fit_one(X.to_dict(orient='records')[0], y)

    def set_Blinds(self, blinds):
        self._blinds = blinds

    def set_position_Blinds(self, position):
        self._blinds.set_position(position)

    def get_position_Blinds(self):
        return self._blinds.get_position()

    def add_Sensor(self, sensor):
        if len(self._sensors) < self._number_of_sensors:
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

    def add_Metrics(self, metric):
        if len(self._metrics) < self._number_of_metrics:
            self._metrics[metric.get_unique_id()] = metric

    def update_Metrics(self, y_true, y_pred, mqtt_component):
        for metric in self._metrics:
            self._metrics[metric].update_metric(y_true, y_pred)
            mqtt_component._logger.log('debug', "Sending message to topic: " + self._metrics[metric].get_value_topic() + " with payload: " + str(round(self._metrics[metric].get_value(), 2)))
            mqtt_component.publish_to_topic(
                self._metrics[metric].get_value_topic(), round(self._metrics[metric].get_value(), 2), 1)

    def get_Metrics(self):
        return self._metrics

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
        if self._blinds and self._switch and len(self._sensors) == self._number_of_sensors and len(self._metrics) == self._number_of_metrics:
            return True
        return False

    def on_position_change(self, client, userdata, msg):
        userdata['logger'].log('debug', "Received Blind Position Change from topic: " + msg.topic + ' --> ' + str(msg.payload.decode()))
        self.set_position_Blinds(int(msg.payload.decode()))

    def on_sensor_state_change(self, client, userdata, msg):
        userdata['logger'].log('debug', "Received Sensor State Change from topic: " +
              msg.topic + ' --> ' + str(msg.payload.decode()))
        self.set_value_Sensor(msg.topic, float(msg.payload.decode()))

    def on_switch_state_change(self, client, userdata, msg):
        message = msg.payload.decode()
        userdata['logger'].log('debug', "Received Switch State Change from topic: " +
              msg.topic + ' --> ' + message)
        if (dt.datetime.now() >= self._date_of_birth + self._learning_time):
            self.set_state_Switch(message)
        elif message == "ON":
            userdata['alt_client'].publish(
                topic=self._switch.get_command_topic(), payload="OFF", qos=1)
    
    def log_message(self, level, message):
        self._logger.log(level, message)

