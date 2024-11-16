import random
import os
import json
import time
import datetime
import requests

from multiprocessing import Process, Value
from base64 import b64encode
from dotenv import load_dotenv
from paho.mqtt import client as mqtt_client

CPU_TEMP_MAX_C: int = 100
FREEZER_TEMP_MAX_C: int = -9
FREEZER_TEMP_MIN_C: int = -29
FRIDGE_TEMP_MAX_C: int = 4
FRIDGE_TEMP_MIN_C: int = 0

c_username = ""
c_password = ""
c_broker = ""
c_port = 0
c_topic = ""
c_wait_minutes = 0
c_webhook_url = ""
c_webhook_auth = ""
c_webhook_id = ""

most_recent_ping = ""

multiprocess_timer = None
device_online = Value('b', False)

def get_config():
    global c_username
    global c_password
    global c_broker
    global c_port
    global c_topic
    global c_wait_minutes
    global c_webhook_url
    global c_webhook_auth
    global c_webhook_id

    load_dotenv()
    try:
        configs = [
            os.getenv('MQTT_USERNAME'),
            os.getenv('MQTT_PASSWORD'),
            os.getenv('MQTT_BROKER'),
            os.getenv('MQTT_PORT'),
            os.getenv('MQTT_TOPIC'),
            os.getenv('MQTT_WAIT_MINUTES'),
            os.getenv('MATRIX_WEBHOOK_URL'),
            os.getenv('MATRIX_WEBHOOK_AUTH'),
            os.getenv('MATRIX_WEBHOOK_DEVICE_ID'),
        ]

        if configs is not None:
            c_username = configs[0]
            c_password = configs[1]
            c_broker = configs[2]
            c_port = int(configs[3])
            c_topic = configs[4]
            c_wait_minutes = configs[5]
            c_webhook_url = configs[6]
            c_webhook_auth = configs[7]
            c_webhook_id = configs[8]
        else:
            raise Exception("Configuration not found")

        return configs
    except Exception as err:
        print(f"Something went wrong with your environment. Please make sure you have every environment variable set properly.\n{err}")
        return None

def print_fahrenheit(celsius: float):
    fahrenheit = (celsius * 1.8) + 32
    return round(fahrenheit, 2)

def send_message(url, auth_token, message):
    print(f"Sending Matrix message: {message}")

    auth_header = b64encode(auth_token.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }

    json_message = json.dumps({"data": message})

    response = requests.post(url, headers=headers, data=json_message)
    return response

def device_alive_timer():
    global c_wait_minutes

    wait_seconds = (float(c_wait_minutes) * 60) + 10

    try:
        time.sleep(wait_seconds)
        print(f"{c_username} is offline!")
        send_message(c_webhook_url, c_webhook_auth, f"{c_username} is offline!")

        with device_online.get_lock():
            device_online.value = False

    except KeyboardInterrupt:
        print("Killing threads")
        return

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
    global most_recent_ping
    data = json.loads(message)
    most_recent_ping = data

    if data.get("device_id") == c_webhook_id:
        if len(most_recent_ping) < 1:
            matrix_message = "The device has not pinged since the server started."
        else:
            timestamp = datetime.datetime.fromtimestamp(most_recent_ping['timestamp'])
            human_readable_time = timestamp.strftime('%m/%d/%Y %l:%M:%S %p')
            matrix_message = f"The device last pinged at {human_readable_time} with the following data:\n\n"
            for sensor, value in most_recent_ping.items():
                try:
                    value = int(value) / 1000

                    matrix_message += f"{sensor}: {print_fahrenheit(value)} F ({value} C)\n"
                except ValueError:
                    matrix_message += f"{sensor}: {value}\n"

        send_message(c_webhook_url, c_webhook_auth, matrix_message)
    else:
        global multiprocess_timer

        matrix_message: str = ""
        timestamp = datetime.datetime.fromtimestamp(data['timestamp'])
        human_readable_time = timestamp.strftime('%m/%d/%Y %l:%M:%S %p')

        print(f"\nDevice temps at {human_readable_time}")
        for sensor, value in data['sensors'].items():
            sensor_l = sensor.lower()

            try:
                value = int(value) / 1000
                match sensor:
                    case "cpu_temp":
                        if value > CPU_TEMP_MAX_C:
                            matrix_message += f"\nCPU is too hot({value} C)"
                    case sensor_l if "fridge" in sensor:
                        if value > FREEZER_TEMP_MAX_C:
                            matrix_message += f"\n{sensor} is too hot ({print_fahrenheit(value)} F)"
                        if value < FREEZER_TEMP_MIN_C:
                            matrix_message += f"\n{sensor} is too cold ({print_fahrenheit(value)} F)"
                    case sensor_l if "freezer" in sensor:
                        if value > FREEZER_TEMP_MAX_C:
                            matrix_message += f"\n{sensor} is too hot ({print_fahrenheit(value)} F)"
                        if value < FREEZER_TEMP_MIN_C:
                            matrix_message += f"\n{sensor} is too cold ({print_fahrenheit(value)} F)"

                print(f"{sensor} is {value} C ({print_fahrenheit(value)} F)")
            except ValueError:
                matrix_message += f"\nThere is an error with {sensor}"

        if matrix_message:
            print("Sending message to Matrix")
            matrix_message = f"Report from {c_username} at {human_readable_time}{matrix_message}"
            send_message(c_webhook_url, c_webhook_auth, matrix_message)

        if not device_online.value:
            with device_online.get_lock():
                device_online.value = True
            print(f"{c_username} is online!")
            send_message(c_webhook_url, c_webhook_auth, f"{c_username} is online!")

        if multiprocess_timer:
            multiprocess_timer.terminate()

        multiprocess_timer = Process(target=device_alive_timer)
        multiprocess_timer.start()

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
    get_config()
    client = connect_mqtt(c_username, c_password, c_broker, c_port)
    subscribe(client, c_topic)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Disconnecting...")
        client.disconnect()
        print("Exiting application")
        return
    except Exception as err:
        print(f"Something went wrong: {err}")
        client.disconnect()
        if multiprocess_timer:
            multiprocess_timer.terminate()
        return


if __name__ == '__main__':
    main()