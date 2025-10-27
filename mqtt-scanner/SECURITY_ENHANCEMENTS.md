# MQTT Scanner - Security Enhancements Documentation

## Overview
This document describes the DevSecOps and security features implemented in the MQTT Scanner application.

## Features Implemented

### 1. DevSecOps Implementation

#### Logging & Monitoring
- **Structured Logging**: All security events are logged with timestamps and severity levels
- **Security Event Tracking**: Special warnings for critical security findings
- **Audit Trail**: Complete scan history with security assessments

#### Key Logging Features:
```python
logger.warning(f"[SECURITY RISK] {host}:{port} allows anonymous access")
logger.warning(f"[SECURITY RISK] {host}:{port} using insecure port (no TLS)")
```

### 2. Port Security Scanning

#### Secure vs Insecure Port Analysis
- **Port 1883** (Insecure MQTT)
  - Plaintext communication
  - No encryption
  - Automatically flagged as HIGH risk

- **Port 8883** (Secure MQTT/TLS)
  - Encrypted communication
  - Certificate validation
  - Security scoring based on certificate quality

#### Comparison Features:
- Side-by-side comparison of secure vs insecure ports
- Risk level assessment for each port
- Security recommendations based on port type

### 3. TLS/SSL Certificate Analysis

#### Detailed Certificate Information:
- **Common Name** - Certificate subject
- **Organization** - Issuing organization
- **Validity Period** - Start and end dates
- **Expiration Status** - Days until expiry
- **Self-Signed Detection** - Identifies self-signed certificates
- **Certificate Fingerprints** - SHA1 and SHA256 hashes

#### Security Scoring (0-100):
- **100** - Perfect score (valid CA-signed cert, strong cipher)
- **-30** - Self-signed certificate
- **-50** - Expired certificate
- **-40** - Certificate not yet valid
- **-20** - Weak cipher detected
- **-25** - Outdated TLS version (SSLv2, SSLv3, TLSv1, TLSv1.1)
- **-10** - Certificate expiring within 30 days

#### TLS/SSL Details Captured:
```python
{
    'common_name': 'mqtt.example.com',
    'organization': 'Example Corp',
    'valid_from': 'Jan 1 00:00:00 2024 GMT',
    'valid_to': 'Dec 31 23:59:59 2025 GMT',
    'days_until_expiry': 365,
    'self_signed': False,
    'expired': False,
    'tls_version': 'TLSv1.3',
    'cipher': ('ECDHE-RSA-AES256-GCM-SHA384', 'TLSv1.3', 256),
    'fingerprint_sha256': '...',
    'security_score': 100
}
```

### 4. Publisher & Subscriber Identification

#### Publisher Detection:
- Monitors all topics for published messages
- Captures topic name, payload size, QoS level
- Tracks retained messages
- Records message frequency per topic

#### Publisher Information Captured:
```python
{
    'topic': 'sensors/temperature',
    'payload_size': 42,
    'qos': 0,
    'retained': False,
    'client_id_note': 'Unknown - MQTT v3.x limitation'
}
```

#### Subscriber Detection:
- Detects subscribers via $SYS topics
- Identifies client IDs when available
- Tracks scanner's own subscription

#### Subscriber Information:
```python
{
    'client_id': 'mqtt-client-12345',
    'detected_via': '$SYS topics',
    'note': 'Detected via broker statistics'
}
```

#### Topic Discovery:
```python
{
    'sensors/temperature': {
        'first_seen': '2025-10-23T12:00:00',
        'message_count': 15,
        'publishers': []
    }
}
```

### 5. Security Assessment & Risk Scoring

#### Risk Levels:
- **CRITICAL** 🔴 - Anonymous access + active publishers on insecure port
- **HIGH** 🟠 - Insecure port OR multiple TLS issues
- **MEDIUM** 🟡 - Anonymous access allowed
- **LOW** 🟢 - Secure configuration

#### Security Checks:
1. **Port Security**
   - Insecure port (1883) usage
   - Missing TLS encryption

2. **Authentication**
   - Anonymous access detection
   - Authentication requirements

3. **Certificate Validation**
   - Expiration status
   - Self-signed detection
   - Cipher strength
   - TLS version compliance

4. **Active Threats**
   - Unauthorized publishers
   - Exposed topics without ACLs

#### Security Summary Example:
```python
{
    'risk_level': 'CRITICAL',
    'issues': [
        'Using insecure port (1883) - no encryption',
        'Anonymous access is allowed',
        '5 active topics detected',
        '3 publishers detected on unsecured broker'
    ],
    'recommendations': [
        'Migrate to port 8883 with TLS/SSL',
        'Enable authentication and disable anonymous access',
        'Review topic ACLs and implement proper authorization'
    ]
}
```

## UI Enhancements

### Dashboard Features:
1. **Security Risk Column** - Color-coded risk badges
2. **Enhanced Details Panel** - Comprehensive security report
3. **Publisher/Subscriber Lists** - Active clients detected
4. **TLS Certificate Details** - Full certificate analysis
5. **Security Recommendations** - Actionable remediation steps

### Report Format:
```
╔════════════════════════════════════════════════════════════╗
║                    MQTT SECURITY SCAN REPORT                ║
╚════════════════════════════════════════════════════════════╝

📍 TARGET INFORMATION
🔒 SECURITY ASSESSMENT
🛡️  ACCESS CONTROL
🔐 TLS/SSL CERTIFICATE ANALYSIS
📤 DETECTED PUBLISHERS
📥 DETECTED SUBSCRIBERS
📋 ACTIVE TOPICS DISCOVERED
🖥️  BROKER INFORMATION
💡 RECOMMENDATIONS
```

## Usage Examples

### Basic Scan (Secure vs Insecure):
```bash
# Scan both ports to compare security
python app.py
# Access: http://127.0.0.1:5000
# Enter target: 127.0.0.1
# Click "Scan"
# Results show both 1883 (insecure) and 8883 (secure)
```

### Deep Scan with Publisher/Subscriber Detection:
```bash
# Enable "Deep scan" toggle
# Set listen duration to 5+ seconds
# Click "Scan"
# View "Details" to see all detected clients
```

### TLS Certificate Analysis:
```bash
# Scan a target with port 8883
# Click "Details" on the 8883 result
# View comprehensive TLS/SSL certificate analysis
# Check security score and recommendations
```

## Security Best Practices Enforced

### DevSecOps Principles:
1. **Shift Left** - Security testing during development
2. **Continuous Monitoring** - Real-time security alerts
3. **Automated Detection** - Automatic vulnerability identification
4. **Actionable Insights** - Clear remediation steps

### Compliance Checks:
- TLS 1.2+ enforcement recommendations
- Certificate expiration monitoring
- Anonymous access detection
- Encryption requirement validation

### Audit & Reporting:
- Timestamped scan results
- Security risk scoring
- Detailed finding reports
- Exportable CSV data

## API Integration

### Security Data in API Response:
```json
{
    "ip": "127.0.0.1",
    "port": 1883,
    "security_summary": {
        "risk_level": "HIGH",
        "issues": [...],
        "recommendations": [...]
    },
    "security_assessment": {
        "anonymous_allowed": true,
        "requires_auth": false,
        "port_type": "insecure"
    },
    "tls_analysis": {...},
    "publishers": [...],
    "subscribers": [...],
    "topics_discovered": {...}
}
```

## Future Enhancements

### Planned Features:
- [ ] MQTT v5 support for enhanced client tracking
- [ ] ACL configuration testing
- [ ] Brute force protection testing
- [ ] QoS compliance checking
- [ ] Will message detection
- [ ] Session persistence analysis
- [ ] Client banner grabbing
- [ ] Automated remediation scripts
- [ ] Integration with SIEM systems
- [ ] PDF report generation

## Conclusion

This MQTT Scanner now provides comprehensive DevSecOps capabilities including:
- ✅ Complete TLS/SSL analysis with security scoring
- ✅ Publisher and subscriber detection
- ✅ Secure vs insecure port comparison
- ✅ Risk-based security assessment
- ✅ Actionable security recommendations
- ✅ Comprehensive audit logging

The scanner helps identify MQTT broker vulnerabilities and provides clear guidance for securing IoT infrastructure.
