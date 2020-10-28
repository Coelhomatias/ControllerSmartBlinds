import paho.mqtt.client as mqtt

class MQTTComponent:

    def __init__(self, identifier, mqtt_host, mqtt_user, mqtt_passwd, mqtt_port, logger, name="MQTTComponent", alt_client=None):
        self._name = name
        self._identifier = identifier
        self._host = mqtt_host
        self._user = mqtt_user
        self._passwd = mqtt_passwd
        self._port = mqtt_port
        self._logger = logger
        self._alt_client = alt_client
        self._client_userdata = {'alt_client':alt_client, 'logger' : self._logger}
        self._client = mqtt.Client(userdata=self._client_userdata)
        self._client.username_pw_set(username=mqtt_user, password=mqtt_passwd)
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        
    
    def get_name(self):
        return self._name

    def get_id(self):
        return self._identifier
    
    def on_connect(self, client, userdata, flags, rc):
        self._logger.log('debug', "Connected with result code: " + str(rc))
    
    def on_disconnect(self, client, userdata, rc):
        self._logger.log('debug', "Disconnected with result code: " + str(rc))
    
    def subscribe_to_topic(self, topic, qos):
        self._client.subscribe(topic, qos)
    
    def publish_to_topic(self, topic, payload, qos):
        self._client.publish(topic, payload, qos)
    
    def add_message_callback(self, topic, function):
        self._client.message_callback_add(topic, function)
    
    def run(self):
        if not self._client.is_connected():
            self._client.connect(self._host, port=self._port)
            self._client.loop_start()
    
    def stop(self):
        if self._client.is_connected():
            self._client.disconnect()
            self._client.loop_stop()