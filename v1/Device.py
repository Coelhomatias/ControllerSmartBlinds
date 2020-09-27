from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch


class Device:

    def __init__(self, name, identifier, availability_topic, number_of_sensors):
        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
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
            values[sensor] = self._sensors[sensor].get_value()
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
