#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import ssl

def publish_insecure():
    client = mqtt.Client("test-publisher-insecure")
    client.connect("127.0.0.1", 1883, 60)
    
    # Publish multi-sensor data with light and motion (insecure broker)
    data = {
        "temp_c": 28.8,
        "hum_pct": 48.0,
        "ldr_pct": 75.3,  # Light sensor (75% brightness)
        "pir": 1,          # Motion detected
        "device": "esp32-multi-sensor",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "ok"
    }
    client.publish("sensors/hanif/multi_insecure", json.dumps(data), qos=0, retain=True)
    print(f"Published to insecure broker: {data}")
    client.disconnect()

def publish_secure():
    client = mqtt.Client("test-publisher-secure")
    client.username_pw_set("testuser", "testpass")
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    client.connect("127.0.0.1", 8883, 60)
    
    # Publish multi-sensor data with all fields (secure broker)
    data = {
        "temp_c": 25.5,
        "hum_pct": 51.4,
        "ldr_pct": 32.8,  # Light sensor (32% brightness)
        "pir": 0,          # No motion
        "device": "esp32-multi-sensor",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "ok"
    }
    client.publish("sensors/hanif/multi_secure", json.dumps(data), qos=0, retain=True)
    print(f"Published to secure broker: {data}")
    client.disconnect()

if __name__ == "__main__":
    print("Publishing test sensor data...")
    publish_insecure()
    publish_secure()
    print("Done!")
