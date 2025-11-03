#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import ssl

received_messages = []

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected successfully")
        # Subscribe to all topics
        client.subscribe("#", qos=0)
        print("📥 Subscribed to all topics (#)")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        print(f"📨 Topic: {msg.topic}")
        print(f"   Payload: {payload_str}")
        print(f"   Retained: {msg.retain}")
        try:
            payload_json = json.loads(payload_str)
            print(f"   JSON: {payload_json}")
        except:
            pass
        print()
        received_messages.append({
            'topic': msg.topic,
            'payload': payload_str,
            'retained': msg.retain
        })
    except Exception as e:
        print(f"❌ Error processing message: {e}")

# Test insecure broker
print("=== Testing Insecure Broker (1883) ===")
try:
    client1 = mqtt.Client(client_id="test-retained-1883", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
except:
    client1 = mqtt.Client(client_id="test-retained-1883")
client1.on_connect = on_connect
client1.on_message = on_message

try:
    client1.connect("127.0.0.1", 1883, 60)
    client1.loop_start()
    time.sleep(3)  # Wait for retained messages
    client1.loop_stop()
    client1.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n✅ Received {len(received_messages)} messages from insecure broker\n")
received_messages = []

# Test secure broker
print("=== Testing Secure Broker (8883) ===")
try:
    client2 = mqtt.Client(client_id="test-retained-8883", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
except:
    client2 = mqtt.Client(client_id="test-retained-8883")
client2.username_pw_set("testuser", "testpass")
client2.tls_set(cert_reqs=ssl.CERT_NONE)
client2.tls_insecure_set(True)
client2.on_connect = on_connect
client2.on_message = on_message

try:
    client2.connect("127.0.0.1", 8883, 60)
    client2.loop_start()
    time.sleep(3)  # Wait for retained messages
    client2.loop_stop()
    client2.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n✅ Received {len(received_messages)} messages from secure broker")
