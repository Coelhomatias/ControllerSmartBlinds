import paho.mqtt.client as mqtt
import json

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("controller/discover/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    parsed = json.loads(msg.payload.decode())
    print(json.dumps(parsed, indent=3, sort_keys=True))

client = mqtt.Client()
client.username_pw_set(username="Coelhomatias",password="lf171297")
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.0.2")


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()