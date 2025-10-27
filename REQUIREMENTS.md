# Functional Requirements for MQTT Scanner Tool

This document outlines the functional requirements for the MQTT Scanner Tool, derived from the project report and user specifications.

## Core Scanning Functionality

1.  **Network Discovery:**
    * Scan local networks (specified by IP address or subnet, e.g., 192.168.1.0/24) to identify potential MQTT brokers.
    * Probe standard MQTT ports: 1883 (insecure) and 8883 (secure/TLS).
2.  **Connection Testing:**
    * Attempt connections to identified open ports.
    * Determine if a connection is successful or refused.
3.  **TLS/SSL Detection:**
    * Specifically check if port 8883 requires a TLS/SSL handshake.
    * Report TLS/SSL status (e.g., required, not required, handshake error).
    * Retrieve and display basic TLS certificate information (snippet) for secure ports.
4.  **Authentication Testing:**
    * Attempt anonymous (no credentials) connection.
    * Attempt connection with user-provided credentials (username/password).
    * Classify authentication status (e.g., Open/No Auth, Auth Required, Auth Success, Auth Failed).
5.  **Topic/Role Identification (Basic):**
    * Connect to accessible brokers (where authentication succeeds or is not required).
    * Subscribe to wildcard topic (`#`) briefly to capture published messages.
    * Identify clients acting as **publishers** and the **topics** they publish to during the capture period.
    * _(Note: Reliable subscriber identification is complex and deferred)_
    * Attempt to probe standard broker status topics (`$SYS/#`) for system information (e.g., client counts).

## User Interface and Reporting

6.  **Web Dashboard (Flask):**
    * Provide a user-friendly web interface for initiating scans and viewing results.
    * Require user login/authentication to access the dashboard.
    * Display scan results in a clear table format, including: IP, Port, Connection Result, Security Classification (TLS status, Auth status), Topics/Publishers found, Timestamp.
    * Allow users to input target IP/subnet and optional credentials.
    * Show scan status updates (idle, scanning, finished, error).
    * Display detailed information (TLS cert snippet, $SYS probe results) for selected scan results.
7.  **API (Flask):**
    * Provide API endpoints (`/api/scan`, `/api/results`) protected by an API key.
    * `/api/scan`: Accepts target and credentials, triggers the Python scanner, returns results (including enriched data like TLS info and topics).
    * `/api/results`: Returns the latest scan results stored (e.g., from CSV).
8.  **Data Export:**
    * Save scan results automatically to a CSV file (`mqtt_scan_report.csv`).
    * Provide a button on the dashboard to download the latest results as a CSV file.
9.  **Laravel Integration (Optional/Demo):**
    * Provide a Laravel frontend (`dashboard.blade.php`) that can display data fetched from the Flask API endpoints.
    * Include controllers (`MqttScannerController.php`) to proxy requests to the Flask backend.

## Security

10. **Application Security:**
    * Implement basic user authentication for the web dashboard.
    * Implement API key authentication for backend API endpoints.

## Non-Functional Requirements

11. **Lightweight:** The core scanning logic should be efficient and runnable on standard hardware.
12. **Platform:** Primarily target Linux (Kali tested) and Windows, developed in Python.
13. **Modularity:** Codebase organized into distinct modules (scanning, probing, detection, reporting, UI).
14. **Usability:** GUI should be intuitive for users with varying technical expertise.