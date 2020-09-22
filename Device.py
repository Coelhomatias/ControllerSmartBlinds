from cover_classes import Blinds
from cover_classes import Sensor
from cover_classes import Switch

class Device:

    def __init__(self, name, identifier, availability_topic):
        self._name = name
        self._identifier = identifier
        self._availability_topic = availability_topic
    
    def get_name(self):
        return self._name
    
    def get_id(self):
        return self._identifier
    
    def get_availability_topic(self):
        return self._availability_topic
    


