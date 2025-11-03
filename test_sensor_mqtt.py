#!/usr/bin/env python3
"""
Quick test to see if we can connect to MQTT and read sensor data
"""
import paho.mqtt.client as mqtt
import json
import time

messages_received = []

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("Subscribing to sensors/#")
        client.subscribe("sensors/#")
    else:
        print(f"Connection failed with code: {rc}")

def on_message(client, userdata, msg):
    print(f"Received on {msg.topic}: {msg.payload.decode()}")
    messages_received.append({
        'topic': msg.topic,
        'payload': msg.payload.decode()
    })

# Test insecure broker (1883)
print("=" * 50)
print("Testing INSECURE broker (127.0.0.1:1883)")
print("=" * 50)
client = mqtt.Client("test-sensor-reader")
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()

    # Listen for 5 seconds
    time.sleep(5)

    client.loop_stop()
    client.disconnect()

    print(f"\nReceived {len(messages_received)} messages:")
    for msg in messages_received:
        print(f"  {msg['topic']}: {msg['payload']}")

    # Parse sensor data
    print("\n" + "=" * 50)
    print("Parsed Sensor Data:")
    print("=" * 50)
    for msg in messages_received:
        try:
            data = json.loads(msg['payload'])
            if 'temp_c' in data or 'temperature' in data:
                print(f"Topic: {msg['topic']}")
                print(f"  Temperature: {data.get('temp_c', data.get('temperature', 'N/A'))}°C")
                print(f"  Humidity: {data.get('hum_pct', data.get('humidity', 'N/A'))}%")
                if 'ldr_pct' in data:
                    print(f"  Light: {data.get('ldr_pct')}%")
                if 'pir' in data:
                    print(f"  Motion: {data.get('pir')}")
                if 'device' in data:
                    print(f"  Device: {data.get('device')}")
        except json.JSONDecodeError:
            print(f"Non-JSON payload on {msg['topic']}: {msg['payload']}")

except Exception as e:
    print(f"Error: {e}")
