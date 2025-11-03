# 🚀 MQTT Security Scanner - Quick Start Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [ESP32 Setup (Hardware)](#esp32-setup-hardware)
4. [Start MQTT Brokers](#start-mqtt-brokers)
5. [Start Laravel Application](#start-laravel-application)
6. [Access the System](#access-the-system)
7. [Testing the System](#testing-the-system)
8. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

Before starting, make sure you have installed:

### 1. **Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop
   - Verify installation: Open terminal/command prompt and run:
     ```bash
     docker --version
     docker compose version
     ```

### 2. **Arduino IDE**
   - Download from: https://www.arduino.cc/en/software
   - Install Arduino IDE
   - Install required libraries (explained in [ESP32 Setup](#esp32-setup-hardware))

### 3. **PHP & Composer** (for Laravel)
   - PHP 8.2 or higher
   - Composer (PHP package manager)
   - Download from: https://getcomposer.org/download/

### 4. **Node.js** (for frontend assets)
   - Download from: https://nodejs.org/
   - Version 18 or higher recommended

---

## 🔧 Installation Steps

### Step 1: Install Dependencies

Open terminal/command prompt in the project root directory and run:

```bash
# Install PHP dependencies
composer install

# Install Node.js dependencies
npm install

# Copy environment file
copy .env.example .env    # On Windows
# OR
cp .env.example .env      # On Mac/Linux

# Generate application key
php artisan key:generate

# Create database tables
php artisan migrate
```

### Step 2: Configure Environment

Edit the `.env` file and update these settings:

```env
APP_NAME="MQTT Security Scanner"
APP_ENV=local
APP_DEBUG=true
APP_URL=http://127.0.0.1:8000

DB_CONNECTION=sqlite
# (SQLite database will be created automatically)

# MQTT Broker Settings (default - no need to change)
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_SECURE_PORT=8883
```

---

## 🔌 ESP32 Setup (Hardware)

### Hardware Requirements:
- **ESP32 Development Board**
- **DHT11 Temperature & Humidity Sensor**
- **LDR (Light Dependent Resistor)** + 10kΩ resistor
- **PIR Motion Sensor (HC-SR501)**
- Jumper wires
- Breadboard

### Wiring Diagram:

```
ESP32 Pin Connections:
├─ DHT11 Sensor
│  ├─ VCC  → 3.3V
│  ├─ GND  → GND
│  └─ DATA → GPIO 4
│
├─ LDR Sensor (Voltage Divider)
│  ├─ LDR  → 3.3V ──┐
│  └─ GND  ← 10kΩ ──┴─ GPIO 34 (ADC)
│
└─ PIR Sensor
   ├─ VCC  → 5V
   ├─ GND  → GND
   └─ OUT  → GPIO 27
```

### Arduino IDE Setup:

1. **Open Arduino IDE**

2. **Install ESP32 Board Support:**
   - Go to: `File → Preferences`
   - Add this URL to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to: `Tools → Board → Boards Manager`
   - Search for "esp32" and install "ESP32 by Espressif Systems"

3. **Install Required Libraries:**
   - Go to: `Sketch → Include Library → Manage Libraries`
   - Install these libraries:
     - **DHT sensor library** by Adafruit
     - **Adafruit Unified Sensor** by Adafruit
     - **PubSubClient** by Nick O'Leary

4. **Open ESP32 Code:**
   - Open file: `esp32_mixed_security.ino`

5. **Configure WiFi and MQTT Settings:**
   
   Find these lines in the code and update them:

   ```cpp
   // ============================================
   // 🔧 CONFIGURATION - CHANGE THESE VALUES
   // ============================================
   
   // WiFi Settings
   const char* ssid = "YOUR_WIFI_NAME";          // ← Change to your WiFi name
   const char* password = "YOUR_WIFI_PASSWORD";  // ← Change to your WiFi password
   
   // MQTT Broker Settings
   const char* mqtt_server = "192.168.1.100";    // ← Change to your computer's IP address
   
   // MQTT Credentials (for secure broker only)
   const char* mqtt_user = "testuser";           // Keep as is (default username)
   const char* mqtt_password = "testpass";       // Keep as is (default password)
   ```

   **How to find your computer's IP address:**
   
   - **Windows:** Open Command Prompt and type `ipconfig`, look for "IPv4 Address"
   - **Mac:** Open Terminal and type `ifconfig | grep inet`, look for your local IP
   - **Linux:** Open Terminal and type `hostname -I`

6. **Upload to ESP32:**
   - Connect ESP32 to your computer via USB
   - Select board: `Tools → Board → ESP32 Dev Module`
   - Select port: `Tools → Port → (select your ESP32 port)`
   - Click **Upload** button (right arrow icon)
   - Wait for "Done uploading" message

7. **Verify ESP32 is Working:**
   - Open Serial Monitor: `Tools → Serial Monitor`
   - Set baud rate to `115200`
   - You should see:
     ```
     Connecting to WiFi...
     WiFi connected!
     IP address: 192.168.x.x
     Connected to MQTT (Secure)
     Connected to MQTT (Insecure)
     Publishing sensor data...
     ```

---

## 🐳 Start MQTT Brokers

The system uses two MQTT brokers (one secure, one insecure) running in Docker.

### Step 1: Navigate to MQTT Brokers Directory

```bash
cd mqtt-brokers
```

### Step 2: Start Docker Containers

```bash
docker compose up -d
```

This will start:
- **Insecure MQTT Broker** on port `1883` (for PIR motion sensor)
- **Secure MQTT Broker** on port `8883` (for DHT11 and LDR sensors)

### Step 3: Verify Brokers are Running

```bash
docker compose ps
```

You should see two containers running:
- `mqtt-brokers-insecure-1`
- `mqtt-brokers-secure-1`

### To Stop Brokers (when needed):

```bash
docker compose down
```

---

## 🌐 Start Laravel Application

### Step 1: Navigate Back to Project Root

```bash
cd ..    # Go back to project root directory
```

### Step 2: Start Laravel Development Server

```bash
php artisan serve
```

You should see:
```
Starting Laravel development server: http://127.0.0.1:8000
```

**Keep this terminal window open** - the server needs to run continuously.

---

## 🎯 Access the System

### Step 1: Open Web Browser

Navigate to: **http://127.0.0.1:8000**

### Step 2: Register an Account

1. Click **"Register"** button
2. Fill in:
   - Name: (your name)
   - Email: (your email)
   - Password: (create a password)
   - Confirm Password: (same password)
3. Click **"Register"**

### Step 3: Login

After registration, you'll be redirected to the dashboard automatically.

---

## 🧪 Testing the System

### Test 1: Scan All Sensors (With Credentials)

1. On the dashboard, scroll to **"Network Scanner"** section
2. Fill in:
   - **Broker IP:** `127.0.0.1` (or your computer's IP)
   - **Insecure Port:** `1883`
   - **Secure Port:** `8883`
   - **Username:** `testuser`
   - **Password:** `testpass`
3. Click **"Scan Network"**

**Expected Result:** You should see **3 sensors**:
- ✅ DHT11 (Secure) - Temperature & Humidity
- ✅ LDR (Secure) - Light Sensor
- ✅ PIR (Insecure) - Motion Sensor

### Test 2: Scan Only Insecure Sensors (Without Credentials)

1. Clear the **Username** and **Password** fields
2. Click **"Scan Network"**

**Expected Result:** You should see **only 1 sensor**:
- ✅ PIR (Insecure) - Motion Sensor

(DHT11 and LDR won't appear because they require authentication)

### Test 3: View Details

1. Click the **"Details"** button on any sensor row
2. A modal will open showing:
   - 📍 Target Information
   - 🔒 Security Assessment
   - 🛡️ Access Control
   - 🔐 TLS/SSL Analysis (for secure sensors)
   - 📤 Publisher Information
   - 📥 Subscriber Information
   - 📊 Current Sensor Data

### Test 4: Export Report

1. After scanning, click **"Export CSV"** button
2. A CSV file will be downloaded with all scan results

---

## 🔍 Understanding the System

### Security Architecture:

| Sensor | Port | Security | Authentication | Encryption |
|--------|------|----------|----------------|------------|
| DHT11  | 8883 | Secure   | Required       | TLS/SSL    |
| LDR    | 8883 | Secure   | Required       | TLS/SSL    |
| PIR    | 1883 | Insecure | Not Required   | None       |

### Topics Published by ESP32:

- `sensors/hanif/dht_secure` - Temperature & humidity data (secure)
- `sensors/hanif/ldr_secure` - Light sensor data (secure)
- `sensors/hanif/pir_insecure` - Motion detection (insecure)

### Data Format:

**DHT11 Secure:**
```json
{"temp": 28.5, "hum": 65.2, "timestamp": 1699000000}
```

**LDR Secure:**
```json
{"light_raw": 1250, "light_percent": 30.5, "timestamp": 1699000000}
```

**PIR Insecure:**
```json
{"motion": "DETECTED", "timestamp": 1699000000}
```

---

## ❗ Troubleshooting

### Problem: ESP32 won't connect to WiFi

**Solution:**
1. Check WiFi credentials in the code
2. Make sure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
3. Check Serial Monitor for error messages

---

### Problem: ESP32 connected but not publishing to MQTT

**Solution:**
1. Verify MQTT brokers are running: `docker compose ps`
2. Check `mqtt_server` IP address matches your computer's IP
3. Verify firewall isn't blocking ports 1883 and 8883
4. Check Serial Monitor for connection errors

---

### Problem: Scan shows "No results" or "0 sensors"

**Solution:**
1. Make sure ESP32 is connected and publishing (check Serial Monitor)
2. Verify Docker containers are running
3. Check if you need credentials:
   - For secure sensors (DHT, LDR): username/password required
   - For insecure sensor (PIR): leave credentials empty
4. Wait 5-10 seconds after ESP32 connects before scanning

---

### Problem: "Connection refused" error when scanning

**Solution:**
1. Check if MQTT brokers are running: `docker compose ps`
2. Restart brokers:
   ```bash
   cd mqtt-brokers
   docker compose down
   docker compose up -d
   ```
3. Make sure ports 1883 and 8883 are not used by other programs

---

### Problem: Laravel server won't start

**Solution:**
1. Check if port 8000 is already in use
2. Try a different port:
   ```bash
   php artisan serve --port=8080
   ```
3. Run `composer install` again if you see missing dependencies

---

### Problem: Docker containers won't start

**Solution:**
1. Make sure Docker Desktop is running
2. Check Docker Desktop logs for errors
3. Try rebuilding containers:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

---

### Problem: Sensors show duplicate data (6 sensors instead of 3)

**Solution:**
This has been fixed! The system now deduplicates by topic. If you still see this:
1. Clear retained messages on brokers
2. Restart Docker containers
3. Power cycle the ESP32

---

## 📞 Support

If you encounter any issues not covered in this guide:

1. Check the Laravel logs:
   ```bash
   tail -f storage/logs/laravel.log
   ```

2. Check Docker logs:
   ```bash
   cd mqtt-brokers
   docker compose logs
   ```

3. Check ESP32 Serial Monitor for connection issues

---

## 🎉 Success Checklist

- ✅ Docker Desktop installed and running
- ✅ Arduino IDE installed with ESP32 support
- ✅ Libraries installed (DHT, PubSubClient)
- ✅ ESP32 code uploaded with correct WiFi/IP settings
- ✅ MQTT brokers running in Docker
- ✅ Laravel server running
- ✅ Can access http://127.0.0.1:8000
- ✅ Successfully registered and logged in
- ✅ Scan shows 3 sensors with credentials
- ✅ Scan shows 1 sensor without credentials
- ✅ Details modal shows security information
- ✅ CSV export works

---

## 📚 Additional Notes

### Default Credentials:
- **MQTT Secure Broker:**
  - Username: `testuser`
  - Password: `testpass`

### Ports Used:
- `1883` - Insecure MQTT Broker
- `8883` - Secure MQTT Broker (TLS)
- `8000` - Laravel Web Application

### System Requirements:
- **RAM:** Minimum 4GB (8GB recommended)
- **Storage:** 2GB free space
- **OS:** Windows 10/11, macOS 10.15+, or Linux
- **Network:** Local WiFi network (2.4GHz for ESP32)

---

**🎯 You're all set! The system is now ready to scan and monitor your IoT sensors.**

If everything works correctly, you should see real-time sensor data from your ESP32 in the dashboard! 🚀
