import time
import os
import random
import json
import psutil
from dotenv import load_dotenv
from paho.mqtt import client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


def get_config():
    load_dotenv()
    try:
        configs = [
            os.getenv('MQTT_USERNAME'),
            os.getenv('MQTT_PASSWORD'),
            os.getenv('MQTT_BROKER'),
            os.getenv('MQTT_PORT'),
            os.getenv('MQTT_TOPIC'),
            os.getenv('MQTT_SLEEP_MINUTES'),
        ]
        return configs
    except Exception as err:
        print(f"Something went wrong with your environment. Please make sure you have every environment variable set properly.\n{err}")
        return None

def create_json_string():
    '''
    json structure should be modified here to fit your needs, and then updated in the server.
    I recommend putting yours below for easy reference in the future.

    {
      "timestamp": #current timestamp,
      "cpu_temp": #cpu temp in C,
      "fridge_1": #fridge temp in C,
      "freezer_1": #freezer temp in C,
      "freezer_2": #freezer temp in C,
    }
    '''

    current_time = time.time()
    cpu_temp = (psutil.sensors_temperatures())['coretemp'][0].current

    data = {
        "timestamp": current_time,
        "cpu_temp": cpu_temp,
        "fridge_1": cpu_temp,
        "freezer_1": cpu_temp,
        "freezer_2": cpu_temp,
    }

    return json.dumps(data)

def connect_mqtt(username, password, broker, port, topic):
    client_id = f"publish-{username}-{random.randint(0, 100)}"

    client = mqtt.Client(client_id = client_id, callback_api_version = CallbackAPIVersion.VERSION2)

    client.username_pw_set(username, password)
    client.connect(broker, port)

    print(f"{client_id} connected to {broker}:{port} as {username}")
    return client

def send_message(client, topic, message):
    client.publish(topic, message)
    print(f"Published {message} to {topic}")

def disconnect_mqtt(client):
    client.disconnect()
    print("Disconnected from MQTT broker")

def control_loop(client, ping_seconds, topic):
    ping_count = 1
    try:
        while True:
            send_message(client, topic, create_json_string())
            ping_count += 1
            time.sleep(ping_seconds)
    except KeyboardInterrupt:
        disconnect_mqtt(client)
        print("Exiting application")
        return

def main():
    config = get_config()
    if config is not None:
        username = config[0]
        password = config[1]
        broker = config[2]
        port = int(config[3])
        topic = config[4]
        ping_seconds = float(config[5])*60
    else:
        print("No config file provided. Exiting.")
        return

    client = connect_mqtt(username, password, broker, port, topic)
    control_loop(client, ping_seconds, topic)

if __name__ == "__main__":
    main()
