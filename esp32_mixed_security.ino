/*
  ESP32 Multi-Sensor MQTT with MIXED Security
  - DHT11 (Temperature & Humidity) → SECURE (port 8883, requires auth)
  - LDR (Light Sensor) → SECURE (port 8883, requires auth)
  - PIR (Motion Sensor) → INSECURE (port 1883, no auth)
  
  This demonstrates two separate MQTT connections:
  1. Secure TLS connection for DHT and LDR
  2. Plain text connection for PIR
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiClient.h>
#include <PubSubClient.h>
#include <DHT.h>
#include "time.h"

// ============================================================================
// WIFI CONFIG
// ============================================================================
const char* ssid     = "RumahKitorangPunya_2.4G";
const char* password = "satusepuluhkali";

// ============================================================================
// MQTT BROKER CONFIG
// ============================================================================
const char* mqtt_server = "192.168.100.140";

// SECURE Connection (for DHT and LDR)
const uint16_t mqtt_port_secure = 8883;
const char* mqtt_user = "testuser";
const char* mqtt_pass = "testpass";

// INSECURE Connection (for PIR)
const uint16_t mqtt_port_insecure = 1883;
// No username/password needed for insecure

// ============================================================================
// MQTT TOPICS
// ============================================================================
const char* topic_dht_secure = "sensors/hanif/dht_secure";      // Secure DHT
const char* topic_ldr_secure = "sensors/hanif/ldr_secure";      // Secure LDR
const char* topic_pir_insecure = "sensors/hanif/pir_insecure";  // Insecure PIR

// ============================================================================
// SENSOR PINS
// ============================================================================
#define DHT_PIN 4
#define DHT_TYPE DHT11
#define LDR_PIN 34
#define PIR_PIN 27

DHT dht(DHT_PIN, DHT_TYPE);

// ============================================================================
// MQTT CLIENTS - Two separate clients
// ============================================================================
WiFiClientSecure secureClient;      // For secure connection (DHT + LDR)
PubSubClient mqttSecure(secureClient);

WiFiClient plainClient;              // For insecure connection (PIR)
PubSubClient mqttInsecure(plainClient);

// ============================================================================
// TIMING
// ============================================================================
unsigned long lastPublishMs = 0;
const unsigned long publishIntervalMs = 3000UL; // Publish every 3 seconds

// ============================================================================
// TLS CERTIFICATE (for secure connection)
// ============================================================================
const char* ca_cert = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDlzCCAn+gAwIBAgIUIrb7gGG1Ky04X5/yVpdacNGsLhEwDQYJKoZIhvcNAQEL
BQAwWzELMAkGA1UEBhMCTVkxDjAMBgNVBAgMBVN0YXRlMQ0wCwYDVQQHDARDaXR5
MQwwCgYDVQQKDANPcmcxCzAJBgNVBAsMAklUMRIwEAYDVQQDDAlsb2NhbGhvc3Qw
HhcNMjUxMDIyMTYzMzEyWhcNMjYxMDIyMTYzMzEyWjBbMQswCQYDVQQGEwJNWTEO
MAwGA1UECAwFU3RhdGUxDTALBgNVBAcMBENpdHkxDDAKBgNVBAoMA0OrZzELMAkG
A1UECwwCSVQxEjAQBgNVBAMMCWxvY2FsaG9zdDCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBANWKyBByvA4dZuAOVTqH0FPrH49a/cYQ+23HDH9mJOOdZyJE
ceGazCFgAd030nteMUP6BuyZfQfvlAuazhTeCBFOtmGNRwL3qHptK2ul3TcZevgY
RaRAu34JyYyQgfM+sx5luS0w3wlOM9pn+GF2bHFTlri2oo4UoZ/OOkxptQ4TeWKE
uU1Z6Esy/12Yp0kCIfWpR2v1sbAbtKCX2wJLAM7xx8jZeLYsGTdwNsZwAAV4tDA8
tPx0uwT+oBuY8ELYUk7NBBz9eTAZqkavJpxKJpIR1UVPhZZi+Vid6Bt4EJGntyA0
8MsH/Xroo41/6ml9D6rHrB8drG5TkpoZkdh6tmkCAwEAAaNTMFEwHQYDVR0OBBYE
FDY/lz4FdwXmGV0mRk2xq858IZJIMB8GA1UdIwQYMBaAFDY/lz4FdwXmGV0mRk2x
q858IZJIMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAIRhAn5j
IOdkbUtkAfHXIaPtSfQdhvWNVlO/N4poq0e9j/6WOiciE1bSyzksthLg/nO7LQ50
clT1LkwUsAh9o5dcrbUWiu2ICl+qkUYOhK7GANbmUoK0pOMQThUU7xplmjb4YQSH
q6XIUZp6VokFtHV/7x9irhFnlar/93akcC5CHI+rmvpAUKxjeO74ldp1HL0dhyIN
jPtW1ufKS7M+F+6zwzKRyDUy//s7sj465c9JV7r5ndBYXyvtvLU5xCIyypEKuzwM
S+Uaow+QdebofWQH6VQOTjfITNLKkThHViGYa3up84qPpCbE35t6mOy0hdMY9poT
qG4NClKDg4Tjx4k=
-----END CERTIFICATE-----
)EOF";

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

void printMqttError(const char* connectionType, int rc) {
  Serial.printf("[%s] Connection failed, rc=%d - ", connectionType, rc);
  switch (rc) {
    case -4: Serial.println("MQTT_CONNECTION_TIMEOUT"); break;
    case -3: Serial.println("MQTT_CONNECTION_LOST"); break;
    case -2: Serial.println("MQTT_CONNECT_FAILED (Network/TLS)"); break;
    case -1: Serial.println("MQTT_DISCONNECTED"); break;
    case 1: Serial.println("MQTT_CONNECT_BAD_PROTOCOL"); break;
    case 2: Serial.println("MQTT_CONNECT_BAD_CLIENT_ID"); break;
    case 3: Serial.println("MQTT_CONNECT_UNAVAILABLE"); break;
    case 4: Serial.println("MQTT_CONNECT_BAD_CREDENTIALS"); break;
    case 5: Serial.println("MQTT_CONNECT_UNAUTHORIZED"); break;
    default: Serial.println("Unknown error"); break;
  }
}

void setup_wifi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 120) {
    delay(500);
    Serial.print(".");
    tries++;
  }
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("✓ WiFi connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("✗ WiFi connection failed!");
  }
}

void setup_time() {
  Serial.print("Syncing time with NTP servers");
  configTime(8 * 3600, 0, "pool.ntp.org", "time.google.com");
  
  time_t now = time(nullptr);
  int tries = 0;
  while (now < 24 * 3600 && tries < 120) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
    tries++;
  }
  Serial.println();
  
  if (now < 24 * 3600) {
    Serial.println("⚠ Time sync failed - TLS may not work!");
  } else {
    Serial.print("✓ Time synced: ");
    Serial.println(ctime(&now));
  }
}

void reconnect_secure() {
  if (mqttSecure.connected()) return;
  
  Serial.println("\n[SECURE] Attempting MQTT TLS connection...");
  Serial.printf("  Server: %s:%d\n", mqtt_server, mqtt_port_secure);
  Serial.printf("  User: %s\n", mqtt_user);
  
  String clientId = "esp32-secure-" + String(random(0xffff), HEX);
  
  if (mqttSecure.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
    Serial.println("  ✓ SECURE connection established!");
    Serial.println("  → DHT11 and LDR will publish here");
  } else {
    printMqttError("SECURE", mqttSecure.state());
  }
}

void reconnect_insecure() {
  if (mqttInsecure.connected()) return;
  
  Serial.println("\n[INSECURE] Attempting plain MQTT connection...");
  Serial.printf("  Server: %s:%d\n", mqtt_server, mqtt_port_insecure);
  Serial.println("  Auth: None (anonymous)");
  
  String clientId = "esp32-insecure-" + String(random(0xffff), HEX);
  
  // No username/password for insecure connection
  if (mqttInsecure.connect(clientId.c_str())) {
    Serial.println("  ✓ INSECURE connection established!");
    Serial.println("  → PIR sensor will publish here");
  } else {
    printMqttError("INSECURE", mqttInsecure.state());
  }
}

void publishSensors() {
  // Read all sensors
  float temp_c = dht.readTemperature();
  float humidity = dht.readHumidity();
  int ldr_raw = analogRead(LDR_PIN);
  float ldr_pct = (ldr_raw / 4095.0) * 100.0;
  int pir_value = digitalRead(PIR_PIN);
  
  // Check DHT validity
  bool dht_valid = !isnan(temp_c) && !isnan(humidity);
  
  // ========================================================================
  // PUBLISH DHT (SECURE)
  // ========================================================================
  if (mqttSecure.connected() && dht_valid) {
    char payload[128];
    snprintf(payload, sizeof(payload), 
             "{\"temp_c\":%.1f,\"hum_pct\":%.1f}", 
             temp_c, humidity);
    
    if (mqttSecure.publish(topic_dht_secure, payload, true)) {
      Serial.printf("[SECURE DHT] ✓ Published: %s\n", payload);
    } else {
      Serial.println("[SECURE DHT] ✗ Publish failed!");
    }
  } else if (!mqttSecure.connected()) {
    Serial.println("[SECURE DHT] ⚠ Not connected - cannot publish");
  }
  
  // ========================================================================
  // PUBLISH LDR (SECURE)
  // ========================================================================
  if (mqttSecure.connected()) {
    char payload[128];
    snprintf(payload, sizeof(payload), 
             "{\"ldr_pct\":%.1f,\"ldr_raw\":%d}", 
             ldr_pct, ldr_raw);
    
    if (mqttSecure.publish(topic_ldr_secure, payload, true)) {
      Serial.printf("[SECURE LDR] ✓ Published: %s\n", payload);
    } else {
      Serial.println("[SECURE LDR] ✗ Publish failed!");
    }
  } else {
    Serial.println("[SECURE LDR] ⚠ Not connected - cannot publish");
  }
  
  // ========================================================================
  // PUBLISH PIR (INSECURE)
  // ========================================================================
  if (mqttInsecure.connected()) {
    char payload[64];
    snprintf(payload, sizeof(payload), "{\"pir\":%d}", pir_value);
    
    if (mqttInsecure.publish(topic_pir_insecure, payload, true)) {
      Serial.printf("[INSECURE PIR] ✓ Published: %s\n", payload);
    } else {
      Serial.println("[INSECURE PIR] ✗ Publish failed!");
    }
  } else {
    Serial.println("[INSECURE PIR] ⚠ Not connected - cannot publish");
  }
  
  Serial.println("---");
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("  ESP32 Mixed Security MQTT");
  Serial.println("========================================");
  Serial.println("  DHT11 → SECURE (8883, auth required)");
  Serial.println("  LDR   → SECURE (8883, auth required)");
  Serial.println("  PIR   → INSECURE (1883, no auth)");
  Serial.println("========================================\n");
  
  // Initialize sensors
  dht.begin();
  pinMode(PIR_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  analogReadResolution(12);
  
  // Setup WiFi and time
  setup_wifi();
  setup_time();
  
  // Configure SECURE MQTT client (TLS)
  secureClient.setInsecure(); // Accept self-signed certificate
  // Or use: secureClient.setCACert(ca_cert); for proper validation
  mqttSecure.setServer(mqtt_server, mqtt_port_secure);
  mqttSecure.setKeepAlive(30);
  mqttSecure.setSocketTimeout(15);
  
  // Configure INSECURE MQTT client (Plain)
  mqttInsecure.setServer(mqtt_server, mqtt_port_insecure);
  mqttInsecure.setKeepAlive(30);
  mqttInsecure.setSocketTimeout(15);
  
  Serial.println("\nSetup complete! Starting main loop...\n");
}

// ============================================================================
// LOOP
// ============================================================================
void loop() {
  // Maintain both connections
  if (!mqttSecure.connected()) {
    reconnect_secure();
  }
  mqttSecure.loop();
  
  if (!mqttInsecure.connected()) {
    reconnect_insecure();
  }
  mqttInsecure.loop();
  
  // Publish sensors every 3 seconds
  unsigned long now = millis();
  if (now - lastPublishMs >= publishIntervalMs) {
    lastPublishMs = now;
    publishSensors();
  }
  
  delay(100);
}
