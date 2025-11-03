#!/usr/bin/env python3
"""
Quick test publisher to simulate sensor data for testing the MQTT scanner
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully!")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully")

def publish_sensor_data():
    # Test data for insecure broker (port 1883)
    print("Testing insecure broker (port 1883)...")
    client_insecure = mqtt.Client()
    client_insecure.on_connect = on_connect
    client_insecure.on_publish = on_publish
    
    try:
        client_insecure.connect("127.0.0.1", 1883, 60)
        client_insecure.loop_start()
        
        # Publish DHT11 test data
        sensor_data = {
            "temperature": round(random.uniform(20.0, 30.0), 1),
            "humidity": round(random.uniform(40.0, 80.0), 1),
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "dht11_test",
            "status": "ok"
        }
        
        topic = "sensors/hanif/dht11_insecure"
        message = json.dumps(sensor_data)
        
        result = client_insecure.publish(topic, message, qos=1, retain=True)
        result.wait_for_publish()
        
        print(f"Published to {topic}: {message}")
        
        client_insecure.loop_stop()
        client_insecure.disconnect()
        
    except Exception as e:
        print(f"Error with insecure broker: {e}")

    # Test data for secure broker (port 8883)
    print("\nTesting secure broker (port 8883)...")
    client_secure = mqtt.Client()
    client_secure.on_connect = on_connect
    client_secure.on_publish = on_publish
    client_secure.username_pw_set("testuser", "testpass")
    import ssl
    client_secure.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
    client_secure.tls_insecure_set(True)  # Allow self-signed certificates
    
    try:
        client_secure.connect("127.0.0.1", 8883, 60)
        client_secure.loop_start()
        
        # Publish multi-sensor test data
        multi_data = {
            "temperature": round(random.uniform(22.0, 28.0), 1),
            "humidity": round(random.uniform(45.0, 75.0), 1),
            "pressure": round(random.uniform(1000.0, 1020.0), 1),
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "multi_secure_test",
            "status": "ok"
        }
        
        topic = "sensors/hanif/multi_secure"
        message = json.dumps(multi_data)
        
        result = client_secure.publish(topic, message, qos=1, retain=True)
        result.wait_for_publish()
        
        print(f"Published to {topic}: {message}")
        
        client_secure.loop_stop()
        client_secure.disconnect()
        
    except Exception as e:
        print(f"Error with secure broker: {e}")

if __name__ == "__main__":
    print("Publishing test sensor data...")
    publish_sensor_data()
    print("Done!")