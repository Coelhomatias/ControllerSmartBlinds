from skmultiflow.meta import AdaptiveRandomForestRegressor


class Blinds:

    def __init__(self, name, unique_id, state_topic, command_topic,
                 model=AdaptiveRandomForestRegressor(random_state=43, n_estimators=100,
                                                     grace_period=50, max_features=11, leaf_prediction='mean', split_confidence=0.09, lambda_value=10)):
        self._name = name
        self._unique_id = unique_id
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._position = 100
        self._model = model

    def get_name(self):
        return self._name

    def get_state_topic(self):
        return self._state_topic

    def get_command_topic(self):
        return self._command_topic

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

    def get_position(self):
        return self._position

    def set_position(self, position):
        self._position = position
