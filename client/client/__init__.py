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
        print(f"Something went wrong with your .env file.\n{err}")
        return None

def create_json_string():
    current_time = time.time()
    cpu_temp = (psutil.sensors_temperatures())['coretemp'][0].current

    data = {
        "current_timestamp": current_time,
        "cpu_temp": cpu_temp,
        #Fridge 1
        #Freezer 1
        #Freezer 2
    }

    return json.dumps(data)

def connect_mqtt(username, password, broker, port, topic):
    client_id = f"publish-{username}-{random.randint(0, 100)}"

    client = mqtt.Client(client_id=client_id, callback_api_version=CallbackAPIVersion.VERSION2)

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
        cleanup(client)

def cleanup(client):
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
    #create_json_string()
