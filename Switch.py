class Switch:

    def __init__(self, name, unique_id, state_topic, command_topic, state=False):
        self._name = name
        self._unique_id = unique_id
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._state = state

    def get_name(self):
        return self._name

    def get_state_topic(self):
        return self._state_topic

    def get_command_topic(self):
        return self._command_topic

    def get_state(self):
        return self._state

    def set_state(self, state):
        self._state = state
