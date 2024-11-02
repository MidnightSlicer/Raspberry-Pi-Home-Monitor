import random
import os
import json
import time

from dotenv import load_dotenv
from paho.mqtt import client as mqtt_client

CPU_TEMP_MAX_C: int = 100
FREEZER_TEMP_MAX_C: int = -18 * 1000
FREEZER_TEMP_MIN_C: int = -29 * 1000
FRIDGE_TEMP_MAX_C: int = 4 * 1000
FRIDGE_TEMP_MIN_C: int = 0

last_data = None
device_online = False

def get_config():
    load_dotenv()
    try:
        configs = [
            os.getenv('MQTT_USERNAME'),
            os.getenv('MQTT_PASSWORD'),
            os.getenv('MQTT_BROKER'),
            os.getenv('MQTT_PORT'),
            os.getenv('MQTT_TOPIC'),
            os.getenv('MQTT_ACCEPTED_WAIT_MINUTES'),
            os.getenv('MQTT_WEBHOOK_URL'),
        ]
        return configs
    except Exception as err:
        print(f"Something went wrong with your environment. Please make sure you have every environment variable set properly.\n{err}")
        return None

def print_fahrenheit(celsius_x_1000):
    celsius = celsius_x_1000 / 1000
    fahrenheit = (celsius * 1.8) + 32
    return round(fahrenheit, 2)


def handle_message_new():
    message = """{"device_id": "Garage Pi", "timestamp": 1730581827.1256046, "sensors": {"cpu_temp": 30.0, "fridge_1": -18657, "freezer_1": -23875, "freezer_2": -22874}}"""

    data = json.loads(message)

    for sensor, value in data['sensors'].items():
        match sensor:
            case "cpu_temp":
                if value > CPU_TEMP_MAX_C:
                    print(f"CPU is too hot({value} C)")
            case sensor if "fridge" in sensor:
                if value > FREEZER_TEMP_MAX_C:
                    print(f"{sensor} is too hot ({print_fahrenheit(value)} F)")
                if value < FREEZER_TEMP_MIN_C:
                    print(f"{sensor} is too cold ({print_fahrenheit(value)} F)")
            case sensor if "freezer" in sensor:
                if value > FREEZER_TEMP_MAX_C:
                    print(f"{sensor} is too hot ({print_fahrenheit(value)} F)")
                if value < FREEZER_TEMP_MIN_C:
                    print(f"{sensor} is too cold ({print_fahrenheit(value)} F)")

def handle_message(message: str):
    """
    json structure should be modified here to fit your needs in accordance with your client.
    I recommend putting yours below for easy reference in the future.

    {
      "device_id": #device_id,
      "timestamp": #current timestamp,
      "sensors": #{sensor data}
    }
    """

    global last_data
    global device_online

    data = json.loads(message)

    if last_data is None:
        last_data = data
        device_online = True
        print("First sighting")
        print("Current Data:",data)
    else:
        #time_diff_between_pings = time.time() - last_data['timestamp']
        #print(f"There was {time_diff_between_pings} seconds between pings.")
        print("hey I've seen you before")
        print("Current Data:", data)
        print("Last Data:   ", last_data)
        # do some work
        last_data = data

def device_check_online(self, wait_minutes):
    wait_seconds = wait_minutes * 60
    time_diff_between_pings = time.time() - self.last_data['timestamp']

    if time_diff_between_pings > wait_seconds:
        print("Device is offline")


def connect_mqtt(username, password, broker, port) -> mqtt_client:
    def on_connect(self, client, userdata, flags, rc):
        if flags == "Success":
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}, {flags}")

    client_id = f'subscribe-{random.randint(0, 100)}'

    client = mqtt_client.Client(client_id = client_id, callback_api_version = mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client, topic):
    def on_message(client, userdata, msg):
        handle_message(msg.payload)

    client.subscribe(topic)
    client.on_message = on_message

def main():
    configs = get_config()
    if configs is not None:
        username = configs[0]
        password = configs[1]
        broker = configs[2]
        port = int(configs[3])
        topic = configs[4]
        wait_minutes = configs[5]
        webhook_url = configs[6]
    else:
        print("No config provided. Exiting.")
        return

    client = connect_mqtt(username, password, broker, port)
    subscribe(client, topic)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Disconnecting...")
        client.disconnect()
        print("Exiting application")
        return


if __name__ == '__main__':
    #main()
    handle_message_new()