class Blinds:

    def __init__(self, name, unique_id, position_topic, command_topic, position=100):
        self._name = name
        self._unique_id = unique_id
        self._position_topic = position_topic
        self._command_topic = command_topic
        self._position = position

    def get_name(self):
        return self._name

    def get_unique_id(self):
        return self._unique_id

    def get_position_topic(self):
        return self._position_topic

    def get_command_topic(self):
        return self._command_topic

    def get_position(self):
        return self._position

    def set_position(self, position):
        self._position = position


class Sensor:

    def __init__(self, name, unique_id, state_topic, units):
        self._name = name
        self._unique_id = unique_id
        self._state_topic = state_topic
        self._units = units
        self._value = 0

    def get_name(self):
        return self._name

    def get_unique_id(self):
        return self._unique_id

    def get_state_topic(self):
        return self._state_topic

    def get_units(self):
        return self._units

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value


class Switch:

    def __init__(self, name, unique_id, state_topic, command_topic, state=False):
        self._name = name
        self._unique_id = unique_id
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._state = state

    def get_name(self):
        return self._name

    def get_unique_id(self):
        return self._unique_id

    def get_state_topic(self):
        return self._state_topic

    def get_command_topic(self):
        return self._command_topic

    def get_state(self):
        return self._state

    def set_state(self, state):
        self._state = state

class Metrics:
    
    def __init__(self, name, unique_id, state_topic, metric):
        self._name = name
        self._unique_id = unique_id
        self._state_topic = state_topic
        self._metric = metric
        self._value_topic = state_topic.replace("state", "value")

    def get_name(self):
        return self._name

    def get_unique_id(self):
        return self._unique_id

    def get_state_topic(self):
        return self._state_topic
    
    def get_value_topic(self):
        return self._value_topic

    def get_metric(self):
        return self._metric
    
    def update_metric(self, y_true, y_pred):
        self._metric.update(y_true, y_pred)

    def get_value(self):
        return self._metric.get()

