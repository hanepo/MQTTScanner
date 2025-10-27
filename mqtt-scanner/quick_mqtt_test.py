"""
Quick MQTT Test Publisher
Simple script to publish a few test messages for scanner testing
"""

import paho.mqtt.client as mqtt_client
import time
import json
from datetime import datetime

BROKER = '127.0.0.1'
PORT = 1883  # Change to 8883 for secure testing

def quick_test():
    """Publish a few test messages quickly"""
    print("🧪 Quick MQTT Publisher Test\n")
    print(f"Connecting to {BROKER}:{PORT}...")

    try:
        client = mqtt_client.Client(
            client_id="quick_test_publisher",
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
        )
    except (AttributeError, TypeError):
        client = mqtt_client.Client(client_id="quick_test_publisher")

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ Connected!\n")
        else:
            print(f"❌ Connection failed: {rc}\n")

    client.on_connect = on_connect

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        time.sleep(1)

        # Publish test messages
        test_messages = [
            ("test/temperature", {"value": 23.5, "unit": "C"}),
            ("test/humidity", {"value": 65, "unit": "%"}),
            ("test/status", {"online": True, "device": "test_sensor"}),
            ("sensors/living_room/temp", {"temperature": 22.1}),
            ("sensors/bedroom/humidity", {"humidity": 58}),
        ]

        print("📤 Publishing test messages...\n")
        for topic, data in test_messages:
            payload = json.dumps({
                **data,
                "timestamp": datetime.utcnow().isoformat()
            })
            result = client.publish(topic, payload, qos=0, retain=True)
            if result.rc == 0:
                print(f"✅ Published to {topic}: {payload}")
            else:
                print(f"❌ Failed to publish to {topic}")
            time.sleep(0.5)

        print("\n✅ Test messages published!")
        print("\n💡 Now run your scanner to detect these topics!")
        print("   The messages are RETAINED, so they'll appear even if the scanner runs later.\n")

        client.loop_stop()
        client.disconnect()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()
