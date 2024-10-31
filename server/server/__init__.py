import random
import os
import json
import time

from dotenv import load_dotenv
from paho.mqtt import client as mqtt_client

FREEZER_TEMP_MAX_C: int = -18
FREEZER_TEMP_MIN_C: int = -29
FRIDGE_TEMP_MAX_C: int = 4
FRIDGE_TEMP_MIN_C: int = 0

last_data: dict = {}
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

def handle_message(message):
    '''
    json structure should be modified here to fit your needs in accordance with your client.
    I recommend putting yours below for easy reference in the future.

    {
      "timestamp": #current timestamp,
      "cpu_temp": #cpu temp in C,
      "fridge_1": #fridge temp in C,
      "freezer_1": #freezer temp in C,
      "freezer_2": #freezer temp in C,
    }
    '''

    global last_data
    global device_online

    print(message)
    data = json.loads(message)

    if bool(last_data):
        last_data = data
        device_online = True
        print("First sighting")
    else:
        #time_diff_between_pings = time.time() - last_data['timestamp']
        #print(f"There was {time_diff_between_pings} seconds between pings.")
        print(last_data)

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
    client.loop_forever()


if __name__ == '__main__':
    main()
