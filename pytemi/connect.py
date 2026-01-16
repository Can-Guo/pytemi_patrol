#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MQTT Connection Helper Function


"""
from datetime import datetime

import paho.mqtt.client as mqtt
import socket
import time


def _on_connect(client, userdata, flags, rc, *args, **kwargs):
    """Connect to MQTT broker and subscribe to topics"""
    # Handle both paho-mqtt 1.x and 2.x client_id formats
    try:
        client_id_str = client._client_id.decode("ascii") if isinstance(client._client_id, bytes) else str(client._client_id)
    except:
        client_id_str = "Unknown"
    
    print(
        "[STATUS] Connected to: {} (rc:{})".format(
            client_id_str, str(rc)
        )
    )

    # subscribing in on_connect() means that if we lose the connection and
    # reconnect, then subscriptions will be renewed
    client.subscribe("temi/#")


def _on_disconnect(client, userdata, rc, *args, **kwargs):
    """Disconnect from MQTT broker"""
    # Handle both paho-mqtt 1.x and 2.x client_id formats
    try:
        client_id_str = client._client_id.decode("ascii") if isinstance(client._client_id, bytes) else str(client._client_id)
    except:
        client_id_str = "Unknown"
    
    print(
        "[STATUS] Disconnected from: {} (rc:{})".format(
            client_id_str, str(rc)
        )
    )
    client.loop_stop()


def _on_message(client, userdata, msg):
    """Print out any topics that have no callbacks"""
    print("[{}][SUB] {} {}".format(now(), msg.topic, str(msg.payload)))


def connect(host, port, username=None, password=None):
    """Connect to MQTT broker"""
    client_id = socket.gethostname() + "-" + datetime.now().strftime("%Y%m%d%H%M%S")

    # create a new MQTT client instance compatible with paho-mqtt 2.x
    try:
        # Try paho-mqtt 2.x style with VERSION2
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, 
                           client_id=client_id,
                           protocol=mqtt.MQTTv311)
    except (AttributeError, TypeError):
        # Fall back to paho-mqtt 1.x style
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

    # attach general callbacks
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect

    # set username and password
    if username and password:
        client.username_pw_set(username=username, password=password)

    # connect to MQTT broker
    try:
        client.connect(host=host, port=port, keepalive=60)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        raise

    # start listening to topics
    client.loop_start()

    # wait for client to connect
    # TODO check using on_connect()
    time.sleep(2)

    return client


if __name__ == "__main__":
    # connect to the MQTT server
    mqtt_client = connect("test.mosquitto.org", 1883)
