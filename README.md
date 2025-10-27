# MQTT Security Scanner

A comprehensive security scanning tool for MQTT brokers with DevSecOps features, TLS/SSL certificate analysis, and publisher/subscriber detection.

![Security Scanner](https://img.shields.io/badge/MQTT-Security%20Scanner-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Docker](https://img.shields.io/badge/Docker-Required-blue)

---

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Testing](#testing)
- [Security Features](#security-features)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### 🔐 Security Analysis
- ✅ **Port Security Scanning** - Compare secure (8883) vs insecure (1883) ports
- ✅ **TLS/SSL Certificate Analysis** - Detailed certificate validation with security scoring
- ✅ **Authentication Detection** - Identify anonymous access vulnerabilities
- ✅ **Risk Assessment** - Color-coded risk levels (Critical, High, Medium, Low)

### 📊 Publisher & Subscriber Detection
- ✅ **Publisher Identification** - Detect active publishers and their topics
- ✅ **Subscriber Tracking** - Identify connected subscribers
- ✅ **Topic Discovery** - Map all active MQTT topics
- ✅ **Message Statistics** - Track message counts and payload sizes

### 🛡️ DevSecOps Integration
- ✅ **Security Logging** - Comprehensive audit trail
- ✅ **Automated Recommendations** - Actionable security advice
- ✅ **Certificate Expiry Warnings** - Proactive monitoring
- ✅ **Compliance Checks** - TLS version and cipher validation

---

## 📦 Prerequisites

### Required Software

1. **Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Windows: Requires Windows 10/11 Pro or Enterprise
   - macOS: macOS 10.15 or newer
   - Linux: Docker Engine + Docker Compose

2. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **Important:** During installation, check "Add Python to PATH"

3. **Git** (Optional - for cloning repository)
   - Download from: https://git-scm.com/downloads

---

## 🚀 Installation Guide

### Step 1: Install Docker Desktop

1. Download Docker Desktop for your operating system
2. Install Docker Desktop
3. **Start Docker Desktop** and wait for it to fully start
4. Verify Docker is running:
   ```bash
   docker --version
   ```
   You should see something like: `Docker version 24.0.x`

---

### Step 2: Extract Project Files

1. Extract the project ZIP file to a folder, for example:
   - Windows: `C:\mqtt-scanner`
   - macOS/Linux: `~/mqtt-scanner`

2. Open a terminal/command prompt in the project folder:
   - **Windows:** Right-click folder → "Open in Terminal" or use Command Prompt
   - **macOS/Linux:** Right-click folder → "Open Terminal Here"

---

### Step 3: Set Up MQTT Brokers (Docker)

The project includes Docker configurations for two MQTT brokers:

```bash
# Navigate to project root
cd path/to/mqtt-scanner

# Start the MQTT brokers
docker-compose up -d
```

This will start:
- **Insecure Broker** - Port 1883 (no encryption)
- **Secure Broker** - Port 8883 (with TLS/SSL)

**Verify brokers are running:**
```bash
docker ps
```

You should see two containers running:
- `mosquitto_insecure`
- `mosquitto_secure`

---

### Step 4: Install Python Dependencies

```bash
# Navigate to the mqtt-scanner directory
cd mqtt-scanner

# Install required Python packages
pip install -r requirements.txt
```

**If you get a "pip not found" error:**
```bash
# Try using python -m pip instead
python -m pip install -r requirements.txt
```

---

## 🎯 Quick Start

### Start the Scanner Application

```bash
# Make sure you're in the mqtt-scanner directory
cd mqtt-scanner

# Start the Flask application
python app.py
```

You should see output like:
```
[2025-10-27 10:00:00] INFO in app: Flask app starting with log level INFO
 * Running on http://127.0.0.1:5000
```

---

### Access the Web Interface

1. Open your web browser
2. Go to: **http://127.0.0.1:5000**
3. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `adminpass`

---

## 📘 Usage

### Running Your First Scan

1. **Login** to the web interface
2. **Enter target IP:**
   - For local testing: `127.0.0.1`
   - For network scan: `192.168.1.100` (single IP)
   - For subnet scan: `192.168.1.0/24` (entire subnet)

3. **Optional settings:**
   - **Username/Password:** If broker requires authentication
   - **Deep Scan:** Enable to capture live messages (recommended)
   - **Listen Duration:** How long to capture messages (3-10 seconds)

4. **Click "Scan"** button

5. **View Results:**
   - Results table shows all discovered brokers
   - **Security Risk** column shows color-coded risk levels:
     - 🔴 **CRITICAL** - Immediate action required
     - 🟠 **HIGH** - Security issues found
     - 🟡 **MEDIUM** - Some concerns
     - 🟢 **LOW** - Secure configuration

6. **Click "Details"** to see comprehensive security report

---

### Understanding the Results

#### Security Risk Levels

| Risk | Meaning | Example |
|------|---------|---------|
| 🔴 **CRITICAL** | Anonymous access + active publishers on insecure port | Unencrypted broker with live data |
| 🟠 **HIGH** | Using insecure port OR multiple TLS issues | Port 1883 in use |
| 🟡 **MEDIUM** | Anonymous access allowed | No authentication required |
| 🟢 **LOW** | Secure configuration | TLS enabled, auth required |

#### Details Panel

The detailed report includes:

```
🔒 SECURITY ASSESSMENT
   - Risk level and issues
   - Security recommendations

🛡️ ACCESS CONTROL
   - Anonymous access status
   - Authentication requirements

🔐 TLS/SSL CERTIFICATE ANALYSIS (for port 8883)
   - Certificate validity
   - Expiration date
   - Self-signed detection
   - Cipher strength

📤 DETECTED PUBLISHERS
   - Active topics
   - Message statistics

📥 DETECTED SUBSCRIBERS
   - Connected clients

📋 ACTIVE TOPICS DISCOVERED
   - All topics with message counts
```

---

## 🧪 Testing

### Testing Without Physical Devices

Since most people don't have ESP32 or IoT devices readily available, we've included test scripts:

#### Quick Test (5 seconds)

```bash
# Run the quick publisher test
python quick_mqtt_test.py
```

This publishes a few test messages to the broker. Then run a scan to see the results.

#### Full Simulation (Continuous)

```bash
# Run the traffic simulator
python test_mqtt_traffic.py
```

Follow the prompts:
1. Choose broker: `1` (insecure), `2` (secure), or `3` (both)
2. Number of devices: `3` (recommended)
3. Duration: `60` seconds

**While the simulator is running:**
1. Go to http://127.0.0.1:5000
2. Run a scan on `127.0.0.1`
3. Enable "Deep scan"
4. Click "Scan"
5. View detailed results

---

## 🔧 Configuration

### Changing Default Credentials

**File:** `mqtt-scanner/app.py`

```python
# Line 84 - Change the default password
VALID_USERS = {'admin': os.environ.get('FLASK_ADMIN_PASS', 'YOUR_NEW_PASSWORD')}
```

**Or set environment variable:**
```bash
# Windows
set FLASK_ADMIN_PASS=your_secure_password

# macOS/Linux
export FLASK_ADMIN_PASS=your_secure_password
```

### Changing Flask Port

**File:** `mqtt-scanner/app.py`

```python
# Line 538 - Change the default port
port = int(os.environ.get('FLASK_PORT', 5000))
```

**Or set environment variable:**
```bash
# Windows
set FLASK_PORT=8080

# macOS/Linux
export FLASK_PORT=8080
```

---

## 🐛 Troubleshooting

### Docker Issues

#### "Cannot connect to Docker daemon"
```bash
# Make sure Docker Desktop is running
# Windows: Check system tray for Docker icon
# macOS: Check menu bar for Docker icon
```

#### "Port already in use"
```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :1883

# macOS/Linux:
lsof -i :1883

# Stop conflicting service or change port in docker-compose.yml
```

### Python Issues

#### "pip: command not found"
```bash
# Use python -m pip instead
python -m pip install -r requirements.txt
```

#### "Python: command not found"
```bash
# Try python3 instead
python3 app.py
```

### Application Issues

#### "CSRF token is missing"
```bash
# Make sure Flask-WTF is installed
pip install flask-wtf

# Restart the application
```

#### "Connection refused" when scanning
```bash
# Check if MQTT brokers are running
docker ps

# Restart brokers if needed
docker-compose restart
```

#### "No topics detected"
```bash
# This is normal if no devices are publishing
# Run the test scripts to simulate traffic:
python quick_mqtt_test.py
```

### Browser Issues

#### Login page not loading
```bash
# Check if Flask is running on port 5000
# Try accessing: http://localhost:5000 instead of 127.0.0.1
```

#### Results not showing
```bash
# Clear browser cache
# Try a different browser
# Check browser console for JavaScript errors (F12)
```

---

## 📁 Project Structure

```
mqtt-scanner/
├── app.py                          # Main Flask application
├── scanner.py                      # Core scanning logic
├── requirements.txt                # Python dependencies
├── templates/
│   ├── dashboard_pretty.html      # Main dashboard UI
│   ├── login.html                 # Login page
│   └── index.html                 # Alternative UI
├── quick_mqtt_test.py             # Quick testing script
├── test_mqtt_traffic.py           # Full traffic simulator
├── SECURITY_ENHANCEMENTS.md       # Security features documentation
├── TESTING_GUIDE.md               # Detailed testing guide
└── mqtt_scan_report.csv           # Scan results (generated)

mqtt-brokers/
├── insecure/
│   ├── config/mosquitto.conf      # Insecure broker config
│   └── data/                      # Broker data
└── secure/
    ├── config/mosquitto.conf      # Secure broker config
    ├── certs/                     # TLS certificates
    └── data/                      # Broker data

docker-compose.yml                  # Docker configuration
README.md                           # This file
```

---

## 🔒 Security Features Details

### Certificate Security Scoring

The scanner assigns a security score (0-100) based on:

| Check | Points Deducted |
|-------|----------------|
| Self-signed certificate | -30 |
| Certificate expired | -50 |
| Certificate not yet valid | -40 |
| Weak cipher (DES, RC4, MD5) | -20 |
| Outdated TLS (SSLv2, SSLv3, TLSv1, TLSv1.1) | -25 |
| Expiring within 30 days | -10 |

**Score Interpretation:**
- **90-100:** Excellent security
- **70-89:** Good security (minor issues)
- **50-69:** Fair security (needs improvement)
- **Below 50:** Poor security (immediate action required)

---

## 📞 Support

### Common Questions

**Q: Do I need physical IoT devices to test this?**
A: No! Use the included test scripts (`quick_mqtt_test.py` or `test_mqtt_traffic.py`)

**Q: Can I scan remote MQTT brokers?**
A: Yes! Enter the remote IP address or hostname in the target field

**Q: Will this work on my network?**
A: Yes, as long as:
- You have network access to the MQTT brokers
- Ports 1883/8883 are not blocked by firewall
- You have proper permissions to scan the network

**Q: Is this safe to use in production?**
A: The scanner is read-only and doesn't modify broker settings. However:
- Always get permission before scanning production systems
- Use during maintenance windows for busy brokers
- Be aware that scanning may briefly increase broker load

**Q: Can I export the results?**
A: Yes! Click the "Export CSV" button on the dashboard

---

## 📝 Default Credentials & Ports

### Web Interface
- **URL:** http://127.0.0.1:5000
- **Username:** `admin`
- **Password:** `adminpass`

### MQTT Brokers (Docker)
- **Insecure Broker**
  - Port: `1883`
  - Authentication: Disabled (anonymous allowed)

- **Secure Broker**
  - Port: `8883`
  - TLS: Enabled (self-signed certificate)
  - Authentication: Disabled (anonymous allowed)

---

## 🎓 Tutorial Videos & Resources

### Step-by-Step Video Guide
*(Coming soon - Add your tutorial video link here)*

### Additional Documentation
- [Security Features Documentation](mqtt-scanner/SECURITY_ENHANCEMENTS.md)
- [Detailed Testing Guide](mqtt-scanner/TESTING_GUIDE.md)
- [MQTT Protocol Basics](https://mqtt.org/)
- [Docker Documentation](https://docs.docker.com/)

---

## ⚠️ Important Notes

1. **Change Default Credentials** in production environments
2. **Docker Desktop must be running** before starting MQTT brokers
3. **Firewall permissions** may be required for network scanning
4. **Test scripts** create retained messages - restart brokers to clear
5. **Python PATH** must be configured during Python installation

---

## 🚦 Quick Reference Commands

### Start Everything
```bash
# 1. Start Docker Desktop (GUI application)
# 2. Start MQTT brokers
docker-compose up -d

# 3. Start scanner application
cd mqtt-scanner
python app.py

# 4. Open browser to http://127.0.0.1:5000
```

### Stop Everything
```bash
# Stop scanner application
# Press Ctrl+C in the terminal running app.py

# Stop MQTT brokers
docker-compose down
```

### Run Tests
```bash
# Quick test (5 seconds)
python quick_mqtt_test.py

# Full simulation (60 seconds default)
python test_mqtt_traffic.py
```

### View Logs
```bash
# View MQTT broker logs
docker logs mosquitto_insecure
docker logs mosquitto_secure

# Scanner logs appear in terminal running app.py
```

---

## 📄 License & Credits

This MQTT Security Scanner is provided for educational and security testing purposes.

**Developed by:** [Your Name/Company]

**Technologies Used:**
- Flask (Web Framework)
- Paho-MQTT (MQTT Client Library)
- Eclipse Mosquitto (MQTT Broker)
- Docker (Containerization)
- Bootstrap (UI Framework)

---

## 🎉 Getting Started Checklist

- [ ] Docker Desktop installed and running
- [ ] Python 3.8+ installed
- [ ] Project files extracted
- [ ] MQTT brokers started (`docker-compose up -d`)
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Scanner application started (`python app.py`)
- [ ] Logged in to web interface (http://127.0.0.1:5000)
- [ ] First scan completed successfully
- [ ] Test scripts tested (`quick_mqtt_test.py`)
- [ ] Results reviewed and understood

---

## 📧 Contact

For questions, issues, or feature requests:
- **Email:** [your-email@example.com]
- **GitHub:** [your-github-repo]
- **Documentation:** See `SECURITY_ENHANCEMENTS.md` and `TESTING_GUIDE.md`

---

**Happy Scanning! 🚀**

*Last Updated: October 2025*
