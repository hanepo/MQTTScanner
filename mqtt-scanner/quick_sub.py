#!/usr/bin/env python3
"""
Quick MQTT subscriber that collects retained messages and outputs JSON
Usage: python quick_sub.py <host> <port> [username] [password]
"""
import sys
import json
import paho.mqtt.client as mqtt
import time
import ssl

messages = []
messages_by_topic = {}  # Track unique topics to deduplicate
connected = False

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        connected = True
        client.subscribe("sensors/#")
    else:
        print(json.dumps({"error": f"Connection failed with code {rc}"}))
        sys.exit(1)

def on_message(client, userdata, msg):
    global messages_by_topic
    try:
        payload = json.loads(msg.payload.decode())
        
        # Only keep retained messages OR update with latest message per topic
        # This deduplicates messages for the same topic
        if msg.retain or msg.topic not in messages_by_topic:
            messages_by_topic[msg.topic] = {
                "topic": msg.topic,
                "message": payload,
                "retained": msg.retain
            }
    except:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python quick_sub.py <host> <port> [username] [password]"}))
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3] if len(sys.argv) > 3 else None
    password = sys.argv[4] if len(sys.argv) > 4 else None
    use_tls = (port == 8883)
    
    try:
        client = mqtt.Client()
    except:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    if username:
        client.username_pw_set(username, password)
    
    if use_tls:
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
    
    try:
        client.connect(host, port, 60)
        client.loop_start()
        time.sleep(2)  # Wait for retained messages
        client.loop_stop()
        client.disconnect()
        
        # Convert dictionary to list of unique messages
        unique_messages = list(messages_by_topic.values())
        print(json.dumps({"messages": unique_messages, "count": len(unique_messages)}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
