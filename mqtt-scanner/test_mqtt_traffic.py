"""
MQTT Traffic Simulator for Testing the Scanner
This script simulates IoT devices publishing and subscribing to MQTT topics
"""

import paho.mqtt.client as mqtt_client
import time
import random
import json
from datetime import datetime
import threading

# MQTT Broker Configuration
BROKER_HOST = '127.0.0.1'
BROKER_PORT_INSECURE = 1883
BROKER_PORT_SECURE = 8883

# Simulated device configurations
DEVICES = [
    {
        'name': 'temperature_sensor_living_room',
        'topic': 'home/livingroom/temperature',
        'data_type': 'temperature',
        'interval': 2  # seconds
    },
    {
        'name': 'humidity_sensor_bedroom',
        'topic': 'home/bedroom/humidity',
        'data_type': 'humidity',
        'interval': 3
    },
    {
        'name': 'motion_detector_hallway',
        'topic': 'home/hallway/motion',
        'data_type': 'motion',
        'interval': 5
    },
    {
        'name': 'light_controller_kitchen',
        'topic': 'home/kitchen/light/status',
        'data_type': 'light_status',
        'interval': 4
    },
    {
        'name': 'door_sensor_main',
        'topic': 'home/entrance/door',
        'data_type': 'door_status',
        'interval': 6
    }
]

def generate_sensor_data(data_type):
    """Generate realistic sensor data based on type"""
    timestamp = datetime.utcnow().isoformat()

    data = {
        'timestamp': timestamp,
        'device_type': data_type
    }

    if data_type == 'temperature':
        data['value'] = round(random.uniform(18.0, 28.0), 2)
        data['unit'] = 'celsius'
    elif data_type == 'humidity':
        data['value'] = round(random.uniform(30.0, 70.0), 2)
        data['unit'] = 'percent'
    elif data_type == 'motion':
        data['detected'] = random.choice([True, False])
    elif data_type == 'light_status':
        data['state'] = random.choice(['on', 'off'])
        data['brightness'] = random.randint(0, 100) if data['state'] == 'on' else 0
    elif data_type == 'door_status':
        data['state'] = random.choice(['open', 'closed'])
        data['lock'] = random.choice(['locked', 'unlocked'])

    return data

class MQTTPublisher:
    """Simulated IoT device that publishes to MQTT"""

    def __init__(self, device_config, broker_host, broker_port, use_tls=False):
        self.device_config = device_config
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.use_tls = use_tls
        self.running = False
        self.client = None

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"✅ [{self.device_config['name']}] Connected to broker at {self.broker_host}:{self.broker_port}")
        else:
            print(f"❌ [{self.device_config['name']}] Connection failed with code {rc}")

    def start(self):
        """Start publishing data"""
        self.running = True

        # Create MQTT client
        try:
            self.client = mqtt_client.Client(
                client_id=self.device_config['name'],
                callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
            )
        except (AttributeError, TypeError):
            self.client = mqtt_client.Client(client_id=self.device_config['name'])

        self.client.on_connect = self.on_connect

        # Configure TLS if needed
        if self.use_tls:
            import ssl
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)

        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()

            # Publish loop
            while self.running:
                data = generate_sensor_data(self.device_config['data_type'])
                payload = json.dumps(data)

                result = self.client.publish(
                    self.device_config['topic'],
                    payload,
                    qos=0,
                    retain=False
                )

                if result.rc == 0:
                    print(f"📤 [{self.device_config['name']}] Published to {self.device_config['topic']}: {payload}")
                else:
                    print(f"❌ [{self.device_config['name']}] Failed to publish")

                time.sleep(self.device_config['interval'])

        except Exception as e:
            print(f"❌ [{self.device_config['name']}] Error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop publishing and disconnect"""
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print(f"🛑 [{self.device_config['name']}] Stopped")

class MQTTSubscriber:
    """Simulated client that subscribes to MQTT topics"""

    def __init__(self, client_id, topics, broker_host, broker_port, use_tls=False):
        self.client_id = client_id
        self.topics = topics
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.use_tls = use_tls
        self.client = None
        self.running = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"✅ [SUBSCRIBER: {self.client_id}] Connected to broker")
            for topic in self.topics:
                client.subscribe(topic, qos=0)
                print(f"📥 [SUBSCRIBER: {self.client_id}] Subscribed to {topic}")
        else:
            print(f"❌ [SUBSCRIBER: {self.client_id}] Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            print(f"📨 [SUBSCRIBER: {self.client_id}] Received on {msg.topic}: {payload[:80]}...")
        except Exception as e:
            print(f"❌ [SUBSCRIBER: {self.client_id}] Error processing message: {e}")

    def start(self):
        """Start subscribing"""
        self.running = True

        try:
            self.client = mqtt_client.Client(
                client_id=self.client_id,
                callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
            )
        except (AttributeError, TypeError):
            self.client = mqtt_client.Client(client_id=self.client_id)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        if self.use_tls:
            import ssl
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)

        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_forever()
        except Exception as e:
            print(f"❌ [SUBSCRIBER: {self.client_id}] Error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop subscribing and disconnect"""
        self.running = False
        if self.client:
            self.client.disconnect()
            print(f"🛑 [SUBSCRIBER: {self.client_id}] Stopped")

def main():
    print("=" * 70)
    print("🧪 MQTT TRAFFIC SIMULATOR FOR SCANNER TESTING")
    print("=" * 70)
    print("\nThis script simulates IoT devices publishing to MQTT topics")
    print("Use this to test the scanner's publisher/subscriber detection\n")

    # Choose broker port
    print("Select MQTT broker to test:")
    print("1. Insecure broker (port 1883)")
    print("2. Secure broker (port 8883)")
    print("3. Both (simultaneously)")

    choice = input("\nEnter choice (1/2/3) [default: 1]: ").strip() or "1"

    # Choose number of devices
    num_devices = input(f"\nNumber of simulated devices (1-{len(DEVICES)}) [default: 3]: ").strip()
    num_devices = int(num_devices) if num_devices.isdigit() else 3
    num_devices = min(num_devices, len(DEVICES))

    # Choose duration
    duration = input("\nSimulation duration in seconds [default: 60]: ").strip()
    duration = int(duration) if duration.isdigit() else 60

    print(f"\n🚀 Starting simulation with {num_devices} devices for {duration} seconds...")
    print("⏰ Press Ctrl+C to stop early\n")

    publishers = []
    subscribers = []
    threads = []

    try:
        # Start publishers based on choice
        ports_to_test = []
        if choice == "1":
            ports_to_test = [(BROKER_PORT_INSECURE, False)]
        elif choice == "2":
            ports_to_test = [(BROKER_PORT_SECURE, True)]
        else:
            ports_to_test = [(BROKER_PORT_INSECURE, False), (BROKER_PORT_SECURE, True)]

        for port, use_tls in ports_to_test:
            port_label = "secure" if use_tls else "insecure"
            print(f"\n📡 Starting devices on {port_label} broker (port {port})...\n")

            # Start publishers
            for device_config in DEVICES[:num_devices]:
                publisher = MQTTPublisher(device_config, BROKER_HOST, port, use_tls)
                publishers.append(publisher)
                thread = threading.Thread(target=publisher.start)
                thread.daemon = True
                thread.start()
                threads.append(thread)
                time.sleep(0.5)  # Stagger startup

            # Start a subscriber
            subscriber = MQTTSubscriber(
                client_id=f"data_logger_{port}",
                topics=["home/#"],  # Subscribe to all home topics
                broker_host=BROKER_HOST,
                broker_port=port,
                use_tls=use_tls
            )
            subscribers.append(subscriber)
            thread = threading.Thread(target=subscriber.start)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        print(f"\n✅ Simulation running! Devices are publishing data...")
        print(f"💡 Now run your MQTT scanner to detect these publishers and subscribers!\n")
        print(f"⏱️  Simulation will run for {duration} seconds...\n")

        # Run for specified duration
        time.sleep(duration)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        print("\n🛑 Stopping all devices...")
        for publisher in publishers:
            publisher.stop()
        for subscriber in subscribers:
            subscriber.stop()

        print("\n✅ Simulation completed!")
        print("\n" + "=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"Publishers simulated: {len(publishers)}")
        print(f"Subscribers simulated: {len(subscribers)}")
        print(f"Topics used: {[d['topic'] for d in DEVICES[:num_devices]]}")
        print("\n💡 TIP: Run the scanner now to see the results!")
        print("=" * 70)

if __name__ == "__main__":
    main()
