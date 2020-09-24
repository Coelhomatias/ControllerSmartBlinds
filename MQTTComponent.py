import paho.mqtt.client as mqtt

class MQTTComponent:

    def __init__(self, mqtt_host, mqtt_user, mqtt_passwd, name="MQTTComponent"):
        self._name = name
        self._host = mqtt_host
        self._user = mqtt_user
        self._passwd = mqtt_passwd
        self._client = mqtt.Client()
        self._client.username_pw_set(username=mqtt_user, password=mqtt_passwd)
        self._client.on_connect = self.on_connect
    
    def on_connect(self, client, userdata, flags, rc):
        print(self._name + " connected with result code: " + str(rc))
    
    def subscribe_to_topic(self, topic, qos):
        self._client.subscribe(topic, qos)
    
    def publish_to_topic(self, topic, payload, qos):
        self._client.publish(topic, payload, qos)
    
    def add_message_callback(self, topic, function):
        self._client.message_callback_add(topic, function)
    
    def run(self):
        self._client.connect(self._host)
        self._client.loop_start()
    
    def stop(self):
        self._client.loop_stop()