#!/usr/bin/env python3
"""Clear all retained messages from MQTT brokers"""
import paho.mqtt.client as mqtt
import ssl
import time

def clear_broker(host, port, use_tls=False, username=None, password=None):
    """Connect to broker and clear all retained messages on sensors/# topics"""
    try:
        client = mqtt.Client(f"cleaner-{port}")
    except:
        client = mqtt.Client(f"cleaner-{port}", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    if username:
        client.username_pw_set(username, password)
    
    if use_tls:
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
    
    topics_to_clear = []
    
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"✅ Connected to {host}:{port}")
            client.subscribe("sensors/#")
        else:
            print(f"❌ Connection failed: {rc}")
    
    def on_message(client, userdata, msg):
        if msg.retain:
            topics_to_clear.append(msg.topic)
            print(f"📍 Found retained message: {msg.topic}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(host, port, 60)
    client.loop_start()
    time.sleep(2)  # Wait to receive all retained messages
    client.loop_stop()
    
    # Clear all retained messages
    for topic in topics_to_clear:
        client.publish(topic, None, retain=True)
        print(f"🗑️  Cleared: {topic}")
    
    client.disconnect()
    print(f"✅ Cleared {len(topics_to_clear)} retained messages from {host}:{port}\n")

if __name__ == "__main__":
    print("=== Clearing Test Data from MQTT Brokers ===\n")
    
    # Clear insecure broker
    print("--- Insecure Broker (1883) ---")
    clear_broker("127.0.0.1", 1883)
    
    # Clear secure broker
    print("--- Secure Broker (8883) ---")
    clear_broker("127.0.0.1", 8883, use_tls=True, username="testuser", password="testpass")
    
    print("=== All test data cleared! ===")
    print("Your ESP32 sensor will now publish fresh data.")
