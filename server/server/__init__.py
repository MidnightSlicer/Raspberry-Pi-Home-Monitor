import random

from paho.mqtt import client as mqtt_client

def connect_mqtt(username, password, broker, port, client_id) -> mqtt_client:
    def on_connect(self, client, userdata, flags, rc):
        if flags == "Success":
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}, {flags}")

    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client, topic):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic.")


    client.subscribe(topic)
    client.on_message = on_message

def main():
    broker = "s2.midnightservers.dev"
    port = 1883
    topic = "test"

    username = "pi-server-1"
    password = "Unsubtly0-Juicy4"
    client_id = f'subscribe-{random.randint(0, 100)}'

    client = connect_mqtt(username, password, broker, port, client_id)
    subscribe(client, topic)
    client.loop_forever()


if __name__ == '__main__':
    main()
