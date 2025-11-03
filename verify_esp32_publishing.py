"""
ESP32 MQTT Publishing Verification Script
This script monitors MQTT brokers to verify ESP32 is publishing sensor data correctly.
"""

import paho.mqtt.client as mqtt
import time
import sys
from datetime import datetime

# Configuration matching your Arduino sketch
SECURE_BROKER = "127.0.0.1"
SECURE_PORT = 8883
MQTT_USER = "testuser"
MQTT_PASS = "testpass"
TOPIC_PATTERN = "sensors/#"  # Subscribe to all sensor topics
ESP32_TOPIC = "sensors/faris/multi_secure"  # Your ESP32 publishes here

# Track received messages
messages_received = []
last_message_time = None

def on_connect(client, userdata, flags, rc):
    """Callback when client connects to broker"""
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {SECURE_BROKER}:{SECURE_PORT}")
        print(f"📡 Subscribing to topic: {TOPIC_PATTERN}")
        client.subscribe(TOPIC_PATTERN)
        print("\n🔍 Monitoring for ESP32 sensor data...")
        print(f"   Expected topic: {ESP32_TOPIC}")
        print(f"   Listening for: temperature, humidity, light, motion")
        print("\n" + "="*60)
    else:
        error_messages = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized"
        }
        print(f"❌ Connection failed: {error_messages.get(rc, 'Unknown error')}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback when message is received"""
    global last_message_time, messages_received

    timestamp = datetime.now().strftime("%H:%M:%S")
    last_message_time = time.time()

    # Decode the message
    try:
        payload = msg.payload.decode('utf-8')
    except:
        payload = str(msg.payload)

    # Track message
    messages_received.append({
        'topic': msg.topic,
        'payload': payload,
        'timestamp': timestamp
    })

    # Display message with formatting
    print(f"\n[{timestamp}] 📨 New Message Received")
    print(f"   Topic:   {msg.topic}")
    print(f"   Payload: {payload}")

    # Check if it's from ESP32
    if msg.topic == ESP32_TOPIC:
        print("   ✅ This is from your ESP32!")

        # Try to parse JSON data
        try:
            import json
            data = json.loads(payload)
            print("\n   📊 Sensor Readings:")
            if 'temp_c' in data:
                print(f"      🌡️  Temperature: {data['temp_c']}°C")
            if 'hum_pct' in data:
                print(f"      💧 Humidity: {data['hum_pct']}%")
            if 'ldr_pct' in data:
                print(f"      💡 Light: {data['ldr_pct']:.1f}%")
            if 'pir' in data:
                motion = "DETECTED" if data['pir'] == 1 else "None"
                print(f"      🏃 Motion: {motion}")
            if 'device' in data:
                print(f"      📱 Device: {data['device']}")
        except:
            pass

    print("="*60)

def on_disconnect(client, userdata, rc):
    """Callback when client disconnects"""
    if rc != 0:
        print(f"\n⚠️  Unexpected disconnection (rc={rc})")

def main():
    print("="*60)
    print("ESP32 MQTT Publishing Verification Tool")
    print("="*60)
    print("\n📋 Configuration:")
    print(f"   Broker: {SECURE_BROKER}:{SECURE_PORT}")
    print(f"   Username: {MQTT_USER}")
    print(f"   Expected ESP32 Topic: {ESP32_TOPIC}")
    print(f"   Publish Interval: Every 3 seconds")
    print("\n🔌 Connecting to MQTT broker...")

    # Create MQTT client
    client = mqtt.Client(client_id=f"verify-esp32-{int(time.time())}")
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    # Configure TLS (insecure mode for testing)
    client.tls_set()
    client.tls_insecure_set(True)

    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        # Connect to broker
        client.connect(SECURE_BROKER, SECURE_PORT, 60)

        # Start monitoring
        client.loop_start()

        print("\n💡 Tips:")
        print("   - If you see messages, your ESP32 is publishing correctly!")
        print("   - If no messages appear, check:")
        print("     1. ESP32 is powered on and connected to WiFi")
        print("     2. Serial monitor shows 'Publish SUCCESS'")
        print("     3. IP address matches: 192.168.100.140")
        print("   - Press Ctrl+C to stop monitoring\n")

        start_time = time.time()
        check_interval = 10  # Check every 10 seconds

        while True:
            time.sleep(check_interval)

            # Status update every 10 seconds
            elapsed = int(time.time() - start_time)
            msg_count = len(messages_received)

            if msg_count == 0:
                print(f"\n⏳ [{elapsed}s] Still waiting... No messages received yet.")
                print("   🔍 Make sure your ESP32 is running!")
            elif last_message_time and (time.time() - last_message_time) > 30:
                print(f"\n⚠️  [{elapsed}s] No new messages for 30+ seconds.")
                print("   ESP32 might have stopped publishing.")
            else:
                print(f"\n✅ [{elapsed}s] Monitoring active. {msg_count} messages received.")

    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user.")
        print(f"\n📊 Summary:")
        print(f"   Total messages received: {len(messages_received)}")
        if messages_received:
            print(f"\n   Last 5 messages:")
            for msg in messages_received[-5:]:
                print(f"   [{msg['timestamp']}] {msg['topic']}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.loop_stop()
        client.disconnect()
        print("\n👋 Disconnected from broker.")

if __name__ == "__main__":
    # Check if paho-mqtt is installed
    try:
        import paho.mqtt.client
    except ImportError:
        print("❌ Error: paho-mqtt library not found")
        print("   Install it with: pip install paho-mqtt")
        sys.exit(1)

    main()
