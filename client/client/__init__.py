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
            os.getenv("MONITOR_NAME"),
        ]

        for config in configs:
            if config is None:
                print("Something went wrong with your environment. "
                      f"Please make sure you have each environment variable set properly.")
                return None

        return configs
    except Exception as err:
        print("Something went wrong with your environment. "
              f"Please make sure you have each environment variable set properly.\n{err}")
        return None

def get_sensors():
    load_dotenv()

    try:
        sensor_macs = []
        sensor_string = os.getenv('SENSOR_MACS')

        for sensor in sensor_string.split(','):
            sensor_macs.append(sensor)

        return sensor_macs
    except Exception as err:
        print("Something went wrong with your environment.")

def create_json_string(device_id):
    """
    json structure should be modified here to fit your needs, and then updated in the server.
    I recommend putting yours below for easy reference in the future.

    {
      "device_id": #device_id,
      "timestamp": #current timestamp,
      "sensors": #{sensor data}
    }
    """
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            cpu_temp = f.read().strip()

        sensor_macs = get_sensors()
        sensor_temps = []

        for sensor in sensor_macs:
            with open(f'/sys/bus/w1/devices/{sensor}', 'r') as f:
                sensor_temps.append(f.read().strip())

        current_time = time.time()

        data = {
            "device_id": device_id,
            "timestamp": current_time,
            "sensors": {
                "cpu_temp": cpu_temp,
                "fridge_1": cpu_temp,
                "freezer_1": cpu_temp,
                "freezer_2": cpu_temp
            }
        }
    except Exception as err:
        print(f"Something went wrong.\n{err}")

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

def control_loop(client, ping_seconds, topic, device_id):
    ping_count = 1
    try:
        while True:
            send_message(client, topic, create_json_string(device_id))
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
        device_id = config[6]
    else:
        print("There is an error in the configuration. Exiting.")
        return

    client = connect_mqtt(username, password, broker, port, topic)
    control_loop(client, ping_seconds, topic, device_id)

if __name__ == "__main__":
    #main()
    get_sensors()
