#!/usr/bin/env python3
"""
MQTT Subscriber Tool
Subscribe to MQTT topics and monitor messages
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

class MQTTSubscriber:
    def __init__(self):
        self.messages = []
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
            # Subscribe to all topics by default
            client.subscribe("#")
            print("📡 Subscribed to all topics (#)")
        else:
            print(f"❌ Failed to connect: {rc}")
    
    def on_message(self, client, userdata, msg):
        timestamp = datetime.now()
        topic = msg.topic
        payload = msg.payload.decode('utf-8', errors='ignore')
        
        message_data = {
            'timestamp': timestamp.isoformat(),
            'topic': topic,
            'payload': payload,
            'qos': msg.qos,
            'retain': msg.retain
        }
        
        self.messages.append(message_data)
        
        # Print message
        print(f"📥 [{timestamp.strftime('%H:%M:%S')}] {topic}")
        print(f"    Payload: {payload}")
        print(f"    QoS: {msg.qos}, Retain: {msg.retain}")
        print("-" * 50)
    
    def start_monitoring(self, host, port, topics=None, username=None, password=None, use_tls=False):
        """Start monitoring MQTT messages"""
        print(f"Starting MQTT subscriber on {host}:{port}")
        
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        
        if username and password:
            client.username_pw_set(username, password)
            print(f"Using credentials: {username}")
        
        if use_tls:
            client.tls_set()
            print("Using TLS/SSL")
        
        try:
            client.connect(host, port, 60)
            
            if topics:
                for topic in topics:
                    client.subscribe(topic)
                    print(f"📡 Subscribed to: {topic}")
            
            client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping subscriber...")
            self.save_messages()
            client.disconnect()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def save_messages(self):
        """Save captured messages to file"""
        if self.messages:
            filename = f"mqtt_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.messages, f, indent=2)
            print(f"💾 Saved {len(self.messages)} messages to {filename}")

if __name__ == "__main__":
    subscriber = MQTTSubscriber()
    
    print("MQTT Subscriber Tool")
    print("Press Ctrl+C to stop and save messages")
    print()
    
    # Monitor local insecure broker
    try:
        subscriber.start_monitoring("127.0.0.1", 1883)
    except Exception as e:
        print(f"Error: {e}")