from datetime import datetime as dt
from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch

class Device:

    def __init__(self, name, identifier, availability_topic):
        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
        self._date_of_bith = dt.now()
        self._sensors = {}
    
    def get_name(self):
        return self._name
    
    def get_id(self):
        return self._identifier
    
    def get_availability_topic(self):
        return self._availability_topic
    
    def set_Blinds(self, blinds):
        self._blinds = blinds

    def add_Sensor(self, sensor):
        self._sensors[sensor.get_unique_id()] = sensor
    
    def set_value_Sensor(self, unique_id, value):
        self._sensors[unique_id] = value

    def get_value_Sensor(self, unique_id):
        return self._sensors[unique_id].get_value()
    
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


