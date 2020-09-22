class Sensor:

    def __init__(self, name, unique_id, state_topic, command_topic, units):
        self._name = name
        self._unique_id = unique_id
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._units = units

    def get_name(self):
        return self._name

    def get_state_topic(self):
        return self._state_topic

    def get_command_topic(self):
        return self._command_topic

    def get_units(self):
        return self._units

    def set_value(self, value):
        self._value = value

    def get_value(self, value):
        return self._value
