# MQTT Scanner - Testing Guide

## Why You See "No Topics Published"

You're seeing "No topics published during the brief scan period" because:

1. ✅ **Your MQTT broker is running** (Mosquitto in Docker)
2. ❌ **No devices are connected** - No ESP32, Arduino, or other IoT devices publishing data
3. ❌ **No test clients** - No MQTT clients actively sending messages
4. 📭 **Broker is idle** - The broker is healthy but has no traffic to report

This is **completely normal** for a test environment without physical devices!

## How to Test the Scanner's New Features

I've created two test scripts to simulate MQTT traffic so you can see all the new security features in action:

### Option 1: Quick Test (Recommended for First Try) 🚀

**Script:** `quick_mqtt_test.py`

This publishes a few **retained** test messages that will stay on the broker until deleted.

```bash
# Run the quick test
python quick_mqtt_test.py
```

**Output:**
```
🧪 Quick MQTT Publisher Test
Connecting to 127.0.0.1:1883...
✅ Connected!

📤 Publishing test messages...
✅ Published to test/temperature: {"value": 23.5, "unit": "C", "timestamp": "..."}
✅ Published to test/humidity: {"value": 65, "unit": "%", "timestamp": "..."}
...
```

**Then run your scanner:**
1. Go to http://127.0.0.1:5000
2. Enter target: `127.0.0.1`
3. Click "Scan"
4. Click "Details" on port 1883 result
5. You should see the published topics! 📊

---

### Option 2: Full Simulation (For Comprehensive Testing) 🔬

**Script:** `test_mqtt_traffic.py`

This simulates **5 IoT devices** continuously publishing data (like real sensors).

```bash
# Run the traffic simulator
python test_mqtt_traffic.py
```

**Interactive Setup:**
```
🧪 MQTT TRAFFIC SIMULATOR FOR SCANNER TESTING

Select MQTT broker to test:
1. Insecure broker (port 1883)
2. Secure broker (port 8883)
3. Both (simultaneously)

Enter choice (1/2/3) [default: 1]: 1

Number of simulated devices (1-5) [default: 3]: 3

Simulation duration in seconds [default: 60]: 60
```

**What It Simulates:**
- 🌡️ Temperature sensor (living room)
- 💧 Humidity sensor (bedroom)
- 🚶 Motion detector (hallway)
- 💡 Light controller (kitchen)
- 🚪 Door sensor (entrance)

**Sample Output:**
```
📤 [temperature_sensor_living_room] Published to home/livingroom/temperature: {"timestamp": "...", "value": 23.4, "unit": "celsius"}
📤 [humidity_sensor_bedroom] Published to home/bedroom/humidity: {"timestamp": "...", "value": 58.2, "unit": "percent"}
📨 [SUBSCRIBER: data_logger_1883] Received on home/livingroom/temperature: ...
```

**While This Runs:**
1. Keep the simulator running in one terminal
2. Open your browser to http://127.0.0.1:5000
3. Run a scan on `127.0.0.1`
4. Enable "Deep scan (capture live messages)" toggle
5. Set listen duration to 5-10 seconds
6. Click "Scan"
7. Click "Details" to see all detected publishers! 🎉

---

## What You'll See After Testing

### In the Scanner Results Table:

| IP | Port | Result | Classification | Security Risk | TLS | Actions |
|----|------|--------|----------------|---------------|-----|---------|
| 127.0.0.1 | 1883 | connected | open_or_auth_ok | 🟠 **HIGH** | No | Details |
| 127.0.0.1 | 8883 | ... | ... | ... | Yes | Details |

### In the Details Panel:

```
╔════════════════════════════════════════════════════════════╗
║                    MQTT SECURITY SCAN REPORT                ║
╚════════════════════════════════════════════════════════════╝

📍 TARGET INFORMATION
IP Address: 127.0.0.1
Port: 1883 (Insecure MQTT)
Result: connected
Classification: open_or_auth_ok

🔒 SECURITY ASSESSMENT
Risk Level: 🟠 HIGH

⚠️  Security Issues Found:
   • Using insecure port (1883) - no encryption
   • Anonymous access is allowed
   • 5 active topics detected
   • 3 publishers detected on unsecured broker

💡 Recommendations:
   ✓ Migrate to port 8883 with TLS/SSL
   ✓ Enable authentication and disable anonymous access
   ✓ Review topic ACLs and implement proper authorization

🛡️  ACCESS CONTROL
Anonymous Access: ❌ ALLOWED (Security Risk!)
Authentication: ❌ Not Required
Port Type: ⚠️  Insecure (Plain)

📤 DETECTED PUBLISHERS (3)
   1. Topic: home/livingroom/temperature
      Payload Size: 89 bytes
      QoS: 0, Retained: False
      Note: Unknown - MQTT v3.x limitation

   2. Topic: home/bedroom/humidity
      Payload Size: 82 bytes
      QoS: 0, Retained: False

   3. Topic: test/temperature
      Payload Size: 75 bytes
      QoS: 0, Retained: True

📥 DETECTED SUBSCRIBERS (2)
   1. Client ID: scanner-1730000000
      Note: Scanner client (this connection)

   2. Client ID: data_logger_1883
      Detected via: $SYS topics

📋 ACTIVE TOPICS DISCOVERED (5)
   • home/livingroom/temperature
     First Seen: 2025-10-27T01:10:00
     Message Count: 12

   • home/bedroom/humidity
     First Seen: 2025-10-27T01:10:02
     Message Count: 8

   [... more topics ...]
```

---

## Testing Secure Port (8883) with TLS

To test the TLS certificate analysis:

1. **Run the simulator on secure port:**
   ```bash
   python test_mqtt_traffic.py
   # Choose option 2 (Secure broker - port 8883)
   ```

2. **Scan the secure port:**
   - Scanner will automatically detect both ports (1883 and 8883)
   - Click "Details" on the **8883** result

3. **View TLS Certificate Analysis:**
   ```
   🔐 TLS/SSL CERTIFICATE ANALYSIS
   Certificate Status: ✅ Valid
   Security Score: 70/100

   Certificate Details:
      Common Name: mosquitto
      Organization: N/A
      Valid From: Jan 1 00:00:00 2024 GMT
      Valid To: Dec 31 23:59:59 2025 GMT
      Days Until Expiry: 65
      Self-Signed: ⚠️  Yes
      Expired: ✅ No
      TLS Version: TLSv1.3
      Cipher Suite: ECDHE-RSA-AES256-GCM-SHA384 (TLSv1.3, 256 bits)

   ⚠️  TLS Security Issues:
      • Self-signed certificate detected
   ```

---

## Comparing Secure vs Insecure Ports

Run the simulator with **option 3** (Both ports simultaneously) to see side-by-side comparison:

```bash
python test_mqtt_traffic.py
# Choose option 3
```

**Scan Results Will Show:**

| Port | Security Risk | Key Differences |
|------|---------------|-----------------|
| 1883 | 🔴 **CRITICAL** | No encryption, anonymous access, exposed topics |
| 8883 | 🟡 **MEDIUM** | TLS encrypted, self-signed cert (warning), anonymous access |

---

## Clean Up After Testing

To remove the retained test messages from your broker:

```bash
# Connect to broker with mosquitto_sub and clear retained messages
mosquitto_pub -h 127.0.0.1 -t "test/temperature" -r -n
mosquitto_pub -h 127.0.0.1 -t "test/humidity" -r -n
mosquitto_pub -h 127.0.0.1 -t "test/status" -r -n
```

Or simply restart your Mosquitto container:
```bash
docker restart mosquitto_insecure
docker restart mosquitto_secure
```

---

## Real-World Use Cases

### Scenario 1: ESP32 with DHT22 Sensor
If you had an **ESP32** with a **DHT22 temperature/humidity sensor**:

1. ESP32 connects to broker at `192.168.1.100:1883`
2. Publishes to `home/bedroom/temperature` every 30 seconds
3. Scanner would detect:
   - ✅ Publisher on topic `home/bedroom/temperature`
   - ⚠️  Anonymous access allowed
   - ⚠️  Using insecure port (no encryption)
   - 🔴 Risk Level: HIGH

### Scenario 2: Production IoT Network
For a **production environment**:

1. 50+ IoT devices on `192.168.1.0/24` network
2. Scanner would discover:
   - All active brokers (ports 1883, 8883)
   - All publishers and their topics
   - Security misconfigurations
   - Certificate expiration warnings
   - ACL bypass vulnerabilities

---

## Troubleshooting

### "Connection refused" on port 8883

Make sure your secure Mosquitto broker is running:
```bash
docker ps | grep mosquitto
# Should show both containers running
```

### No $SYS topics detected

Some brokers disable $SYS topics. Enable them in `mosquitto.conf`:
```
sys_interval 10
```

### Subscribers not showing up

- $SYS topic detection depends on broker configuration
- Try running the test simulator with subscribers
- Scanner's own subscription will always show up

---

## Next Steps

1. ✅ **Test the quick script first** - See basic topic detection
2. ✅ **Run the full simulator** - See continuous publishing/subscribing
3. ✅ **Test secure port (8883)** - See TLS certificate analysis
4. ✅ **Enable Deep Scan** - Capture more messages and details
5. ✅ **Compare ports** - See security risk differences
6. 🚀 **Connect real devices** - When you get ESP32/Arduino hardware

---

## Summary

**Without test scripts or real devices:**
- ❌ No topics detected (broker is idle)

**With test scripts:**
- ✅ Publishers detected
- ✅ Subscribers detected
- ✅ Topics discovered
- ✅ Security assessment
- ✅ TLS analysis (on port 8883)
- ✅ Risk scoring
- ✅ Actionable recommendations

**Happy Testing! 🚀**
