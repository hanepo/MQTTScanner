import ssl
import socket, time, datetime
from paho.mqtt import client as mqtt_client
import threading # Added for concurrent listening
import logging
import hashlib
from collections import defaultdict

# Configure logging for DevSecOps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

COMMON_PORTS = [1883, 8883]
TIMEOUT = 2
LISTEN_DURATION = 5 # Seconds to listen for published messages

# --- Store captured messages globally (or pass through context) ---
# Simple approach for demonstration; consider thread-safe structures for production
captured_messages = {} # Key: (host, port), Value: list of (topic, client_id_approx)
capture_lock = threading.Lock()

# Track publishers and subscribers per broker
broker_clients = {} # Key: (host, port), Value: {'publishers': set(), 'subscribers': set(), 'topics': dict}
clients_lock = threading.Lock()

def analyze_tls_certificate(host, port, timeout=3):
    """
    Enhanced TLS/SSL certificate analysis for DevSecOps.
    Returns detailed certificate information including security assessment.
    """
    cert_analysis = {
        'has_tls': False,
        'cert_valid': False,
        'cert_details': {},
        'security_issues': [],
        'security_score': 0,
        'error': None
    }

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert_analysis['has_tls'] = True

                # Get certificate in both formats
                cert_dict = ssock.getpeercert()
                der_cert = ssock.getpeercert(binary_form=True)

                if cert_dict:
                    # Extract detailed certificate information
                    subject = dict(x[0] for x in cert_dict.get('subject', []))
                    issuer = dict(x[0] for x in cert_dict.get('issuer', []))

                    cert_analysis['cert_details'] = {
                        'subject': subject,
                        'issuer': issuer,
                        'common_name': subject.get('commonName', 'N/A'),
                        'organization': subject.get('organizationName', 'N/A'),
                        'valid_from': cert_dict.get('notBefore'),
                        'valid_to': cert_dict.get('notAfter'),
                        'serial_number': cert_dict.get('serialNumber'),
                        'version': cert_dict.get('version'),
                        'tls_version': ssock.version(),
                        'cipher': ssock.cipher()
                    }

                    # Security Assessment
                    security_score = 100

                    # Check if self-signed
                    if subject == issuer:
                        cert_analysis['security_issues'].append('Self-signed certificate detected')
                        cert_analysis['cert_details']['self_signed'] = True
                        security_score -= 30
                    else:
                        cert_analysis['cert_details']['self_signed'] = False

                    # Check expiration
                    try:
                        from datetime import datetime
                        not_after = datetime.strptime(cert_dict.get('notAfter'), '%b %d %H:%M:%S %Y %Z')
                        not_before = datetime.strptime(cert_dict.get('notBefore'), '%b %d %H:%M:%S %Y %Z')
                        now = datetime.utcnow()

                        if now > not_after:
                            cert_analysis['security_issues'].append('Certificate expired')
                            cert_analysis['cert_details']['expired'] = True
                            security_score -= 50
                        elif now < not_before:
                            cert_analysis['security_issues'].append('Certificate not yet valid')
                            cert_analysis['cert_details']['not_yet_valid'] = True
                            security_score -= 40
                        else:
                            cert_analysis['cert_valid'] = True
                            cert_analysis['cert_details']['expired'] = False

                            # Check if expiring soon (within 30 days)
                            days_until_expiry = (not_after - now).days
                            if days_until_expiry < 30:
                                cert_analysis['security_issues'].append(f'Certificate expires in {days_until_expiry} days')
                                security_score -= 10

                            cert_analysis['cert_details']['days_until_expiry'] = days_until_expiry
                    except Exception as date_error:
                        logger.warning(f"Error parsing certificate dates: {date_error}")

                    # Check cipher strength
                    cipher_info = ssock.cipher()
                    if cipher_info:
                        cipher_name = cipher_info[0]
                        if any(weak in cipher_name.upper() for weak in ['DES', 'RC4', 'MD5', 'NULL']):
                            cert_analysis['security_issues'].append(f'Weak cipher detected: {cipher_name}')
                            security_score -= 20

                    # Check TLS version
                    tls_version = ssock.version()
                    if tls_version in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                        cert_analysis['security_issues'].append(f'Outdated TLS version: {tls_version}')
                        security_score -= 25

                    # Calculate fingerprint
                    if der_cert:
                        cert_analysis['cert_details']['fingerprint_sha256'] = hashlib.sha256(der_cert).hexdigest()
                        cert_analysis['cert_details']['fingerprint_sha1'] = hashlib.sha1(der_cert).hexdigest()

                        # Store PEM for reference
                        pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
                        cert_analysis['cert_details']['pem_snippet'] = pem_cert[:500]

                    cert_analysis['security_score'] = max(0, security_score)

    except ssl.SSLError as e:
        cert_analysis['error'] = f'SSL error: {str(e)}'
        logger.error(f"SSL error analyzing {host}:{port} - {e}")
    except socket.timeout:
        cert_analysis['error'] = 'Connection timeout'
    except ConnectionRefusedError:
        cert_analysis['error'] = 'Connection refused'
    except Exception as e:
        cert_analysis['error'] = f'Error: {str(e)}'
        logger.error(f"Error analyzing certificate for {host}:{port} - {e}")

    return cert_analysis

def try_mqtt_connect(host, port, use_tls=False, username=None, password=None, wait_secs=6):
    result = {
        'ip': host,
        'port': port,
        'result': 'unknown',
        'classification': 'unknown',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'publishers': [],
        'subscribers': [],
        'topics_discovered': {},
        'tls_analysis': None,
        'security_assessment': {
            'anonymous_allowed': False,
            'requires_auth': False,
            'port_type': 'insecure' if port == 1883 else 'secure'
        }
    }
    client = None
    client_id = f"scanner-{int(time.time())}" # Use this client_id

    # Track message statistics
    message_stats = defaultdict(lambda: {'count': 0, 'publishers': set(), 'last_payload_size': 0})

    # Add TLS analysis for secure ports
    if use_tls or port == 8883:
        logger.info(f"Analyzing TLS certificate for {host}:{port}")
        result['tls_analysis'] = analyze_tls_certificate(host, port)

    try:
        # Handle both paho-mqtt v1.x and v2.x compatibility
        try:
            # Try paho-mqtt 2.x style first
            client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
        except (AttributeError, TypeError):
            # Fall back to paho-mqtt 1.x style
            client = mqtt_client.Client(client_id=client_id)

        if username:
            client.username_pw_set(username, password)

        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try: client.tls_set_context(ctx)
            except Exception:
                try:
                    client.tls_set()
                    client.tls_insecure_set(True)
                except Exception: pass

        connected = False
        last_rc = None
        connect_error = None
        sys_clients_detected = set()

        def on_connect(c, userdata, flags, rc, properties=None):
            nonlocal connected, last_rc, connect_error
            last_rc = rc
            if rc == 0:
                connected = True
                # Check if anonymous connection succeeded
                if username is None:
                    result['security_assessment']['anonymous_allowed'] = True
                    logger.warning(f"[SECURITY] Anonymous access allowed on {host}:{port}")
                else:
                    result['security_assessment']['requires_auth'] = True

                # Register ourselves as a subscriber
                result['subscribers'].append({
                    'client_id': client_id,
                    'note': 'Scanner client (this connection)'
                })

                try:
                    # Subscribe to all topics upon successful connection
                    c.subscribe("#", qos=0)
                    # Subscribe to $SYS topics to detect other clients
                    c.subscribe("$SYS/broker/clients/#", qos=0)
                    c.subscribe("$SYS/broker/subscriptions/#", qos=0)
                    logger.info(f"[{host}:{port}] Successfully subscribed to # and $SYS topics")
                except Exception as sub_e:
                    logger.error(f"[{host}:{port}] Error subscribing: {sub_e}")
            else:
                connect_error = f"Connection failed with code {rc}"
                if rc == 5:
                    result['security_assessment']['requires_auth'] = True
                    logger.info(f"[{host}:{port}] Authentication required (rc=5)")

        def on_message(c, userdata, msg):
            nonlocal sys_clients_detected
            try:
                topic = msg.topic
                payload = msg.payload.decode('utf-8', errors='replace')

                # Track topics and messages
                message_stats[topic]['count'] += 1
                message_stats[topic]['last_payload_size'] = len(msg.payload)

                # Detect publishers from $SYS topics
                if topic.startswith('$SYS/broker/clients/'):
                    # Extract client ID from $SYS topics
                    parts = topic.split('/')
                    if len(parts) >= 4:
                        client_info = parts[3]
                        sys_clients_detected.add(client_info)
                        logger.debug(f"Detected client from $SYS: {client_info}")

                # Track regular topics (non-$SYS)
                if not topic.startswith('$SYS/'):
                    publisher_info = {
                        'topic': topic,
                        'payload_size': len(msg.payload),
                        'qos': msg.qos,
                        'retained': msg.retain,
                        'client_id_note': 'Unknown - MQTT v3.x limitation'
                    }

                    # Store unique topics
                    if topic not in result['topics_discovered']:
                        result['topics_discovered'][topic] = {
                            'first_seen': datetime.datetime.utcnow().isoformat(),
                            'message_count': 0,
                            'publishers': []
                        }

                    result['topics_discovered'][topic]['message_count'] += 1

                    # Add to publishers list if not already there
                    if publisher_info not in result['publishers']:
                        result['publishers'].append(publisher_info)
                        logger.info(f"[{host}:{port}] Detected publisher on topic: {topic}")

                # Store in global captured_messages for compatibility
                key = (host, port)
                with capture_lock:
                    if key not in captured_messages:
                        captured_messages[key] = []
                    msg_info = {'topic': topic, 'payload': payload[:100]}
                    if msg_info not in captured_messages[key]:
                        captured_messages[key].append(msg_info)

            except Exception as msg_e:
                logger.error(f"Error processing message on {host}:{port}: {msg_e}")

        client.on_connect = on_connect
        client.on_message = on_message # Add message callback

        # Blocking connect might time out before on_connect is called if server is slow/unresponsive
        # Use connect_async and loop_start for better handling
        client.connect(host, port, keepalive=10) # Use keepalive > listen duration
        client.loop_start()

        # Wait for connection or timeout
        connect_timeout = time.time() + wait_secs
        while time.time() < connect_timeout and not connected and connect_error is None:
            time.sleep(0.1)

        if connected:
            result['result'] = 'connected'
            result['classification'] = 'open_or_auth_ok'

            # Listen for messages for a specified duration
            listen_end_time = time.time() + LISTEN_DURATION
            while time.time() < listen_end_time:
                time.sleep(0.2)

            # Add detected $SYS clients to subscribers list
            for client_info in sys_clients_detected:
                if client_info != client_id:  # Don't include ourselves
                    result['subscribers'].append({
                        'client_id': client_info,
                        'detected_via': '$SYS topics'
                    })

            # Retrieve captured messages for this host/port (for backward compatibility)
            key = (host, port)
            with capture_lock:
                if key in captured_messages:
                    # Already stored in result['publishers'], just clean up
                    del captured_messages[key]

            # Generate security summary
            result['security_summary'] = generate_security_summary(result, port, username)

        else:
            result['result'] = 'connect_failed'
            if connect_error:
                result['result'] += f' ({connect_error})'
            if last_rc is not None:
                # result['result'] += f' (rc={last_rc})' # Already included in connect_error if applicable
                result['classification'] = 'not_authorized' if last_rc == 5 else 'not_authorized_or_unreachable'
            else:
                 result['classification'] = 'connect_timeout_or_unreachable' # More specific if no RC received

    except socket.timeout:
        result['result'] = 'error:socket_timeout'
        result['classification'] = 'unreachable_or_firewalled'
    except ConnectionRefusedError:
        result['result'] = 'error:connection_refused'
        result['classification'] = 'unreachable_or_firewalled'
    except OSError as e: # Catch specific network errors like "Network is unreachable"
        result['result'] = f'error:os_error:{str(e)}'
        result['classification'] = 'network_error_or_unreachable'
    except Exception as e:
        result['result'] = f'error:{str(e)}'
        if 'SSL' in str(e) or 'tls' in str(e).lower():
            result['classification'] = 'tls_or_ssl_error'
        # Check for authentication failure specifically if possible (depends on exception details)
        elif 'auth' in str(e).lower():
             result['classification'] = 'not_authorized'
        else:
            result['classification'] = 'error'
    finally:
        try:
            if client is not None:
                client.loop_stop()
                client.disconnect()
        except: pass

    # Log security findings
    if result.get('security_assessment', {}).get('anonymous_allowed'):
        logger.warning(f"[SECURITY RISK] {host}:{port} allows anonymous access")
    if port == 1883 and result.get('classification') == 'open_or_auth_ok':
        logger.warning(f"[SECURITY RISK] {host}:{port} using insecure port (no TLS)")

    return result

def generate_security_summary(result, port, username):
    """
    Generate a security summary for DevSecOps reporting.
    """
    summary = {
        'risk_level': 'LOW',
        'issues': [],
        'recommendations': []
    }

    # Check port security
    if port == 1883:
        summary['issues'].append('Using insecure port (1883) - no encryption')
        summary['recommendations'].append('Migrate to port 8883 with TLS/SSL')
        summary['risk_level'] = 'HIGH'

    # Check anonymous access
    if result.get('security_assessment', {}).get('anonymous_allowed'):
        summary['issues'].append('Anonymous access is allowed')
        summary['recommendations'].append('Enable authentication and disable anonymous access')
        if summary['risk_level'] == 'LOW':
            summary['risk_level'] = 'MEDIUM'

    # Check TLS certificate
    tls_analysis = result.get('tls_analysis', {})
    if tls_analysis and tls_analysis.get('security_issues'):
        summary['issues'].extend(tls_analysis['security_issues'])
        summary['risk_level'] = 'HIGH'

    if tls_analysis and tls_analysis.get('cert_details', {}).get('self_signed'):
        summary['recommendations'].append('Use certificates signed by a trusted CA')

    # Check for exposed topics
    topics_count = len(result.get('topics_discovered', {}))
    if topics_count > 0:
        summary['issues'].append(f'{topics_count} active topics detected')
        summary['recommendations'].append('Review topic ACLs and implement proper authorization')

    # Publishers without authentication
    if result.get('security_assessment', {}).get('anonymous_allowed') and result.get('publishers'):
        summary['issues'].append(f'{len(result["publishers"])} publishers detected on unsecured broker')
        summary['risk_level'] = 'CRITICAL'

    return summary


def scan_ip(ip, creds=None):
    results = []
    for p in COMMON_PORTS:
        s = None # Initialize s
        try:
            # Quick check if port is open before attempting MQTT connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect((ip, p))
            s.close() # Port is open, proceed with MQTT connect attempt

            is_tls = (p == 8883)
            # First try anonymous (no creds)
            res = try_mqtt_connect(ip, p, use_tls=is_tls, wait_secs=4)

            # If anonymous failed and creds provided, try with credentials
            # Only retry if the failure seems auth-related or requires TLS negotiation that might succeed with creds
            retry_needed = res['classification'] in ['not_authorized', 'tls_or_ssl_error', 'not_authorized_or_unreachable', 'connect_timeout_or_unreachable']

            if retry_needed and creds:
                print(f"Retrying {ip}:{p} with credentials...")
                res_with_creds = try_mqtt_connect(ip, p, use_tls=is_tls, username=creds.get('user'), password=creds.get('pass'), wait_secs=4)
                # Prefer positive result or more specific error
                if res_with_creds['classification'] == 'open_or_auth_ok' or res['classification'] == 'unknown':
                     res = res_with_creds
                # If both failed, keep the potentially more informative error (e.g., specific auth failure over timeout)
                elif res_with_creds['classification'] != 'unknown' and res['classification'].endswith('_unreachable'):
                    res = res_with_creds

            results.append(res)

        except (socket.timeout, ConnectionRefusedError, OSError):
             # Port is closed or unreachable at TCP level
            res = {'ip':ip, 'port':p, 'result':'closed_or_unreachable', 'classification':'closed_or_unreachable', 'timestamp': datetime.datetime.utcnow().isoformat(), 'publishers': []}
            results.append(res)
        except Exception as general_e: # Catch any other unexpected error during the port check phase
            print(f"Unexpected error checking port {ip}:{p} - {general_e}")
            res = {'ip':ip, 'port':p, 'result':f'error_port_check:{str(general_e)}', 'classification':'error', 'timestamp': datetime.datetime.utcnow().isoformat(), 'publishers': []}
            results.append(res)
        finally:
             if s: # Ensure socket is closed if it was opened
                 try: s.close()
                 except: pass
    return results

def run_scan(target, creds=None):
    ips = []
    # Basic IP/CIDR handling (only /24 for demo)
    if '/' in target:
        try:
            base, cidr = target.split('/')
            parts = base.split('.')
            if cidr == '24' and len(parts) == 4:
                prefix = '.'.join(parts[:3])
                # Limit scan range for demo purposes (e.g., first 10 IPs)
                # ips = [f"{prefix}.{i}" for i in range(1, 11)] # Scan .1 to .10
                ips = [f"{prefix}.{i}" for i in range(1, 255)] # Full /24 scan
            else:
                 ips = [base] # Treat invalid CIDR as single IP
        except:
             ips = [target] # Fallback if parsing fails
    else:
        ips = [target]

    print(f"Scanning {len(ips)} IP(s)... Target: {target}")
    all_results = []
    # --- Optional: Use threading for faster scanning ---
    threads = []
    results_list = [] # Shared list for thread results

    def scan_worker(ip, creds, results_container):
        try:
            res = scan_ip(ip, creds)
            results_container.extend(res)
        except Exception as e:
            print(f"Error scanning {ip}: {e}")

    for ip in ips:
        thread = threading.Thread(target=scan_worker, args=(ip, creds, results_list))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join() # Wait for all threads to complete

    # --- Original sequential scan ---
    # for ip in ips:
    #     print(f"Scanning {ip}...")
    #     all_results.extend(scan_ip(ip, creds))

    print(f"Scan complete. Found {len(results_list)} results.")
    return results_list # Return results from threads

if __name__ == '__main__':
    # Example usage: Scan localhost, provide credentials
    scan_results = run_scan('127.0.0.1', creds={'user':'testuser','pass':'testpass'})
    import json
    print(json.dumps(scan_results, indent=2))
    # Example usage: Scan a /24 subnet (adjust range in run_scan if needed)
    # scan_results_subnet = run_scan('192.168.1.0/24')
    # print(json.dumps(scan_results_subnet, indent=2))