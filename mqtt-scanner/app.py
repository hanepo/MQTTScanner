# app.py — prettier Flask UI + auth + TLS info + $SYS probe + Topic Capture
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from scanner import run_scan # Assumes scanner.py is in the same directory or accessible via PYTHONPATH
import csv, os, ssl, socket, time, json # Added json
from functools import wraps
from paho.mqtt import client as mqtt_client
from collections import defaultdict
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates')
# IMPORTANT: Change this secret key in production! Use a long, random string.
# You can generate one using: python -c 'import secrets; print(secrets.token_hex(24))'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-weak-secret-key-change-me') # Load from env or use a default

CORS(app, supports_credentials=True) # Allow credentials for session cookies
csrf = CSRFProtect(app)

# Read secret API key from env (default for dev)
FLASK_API_KEY = os.environ.get('FLASK_API_KEY', 'my-very-secret-flask-key-CHANGEME')

# --- Rate Limiting Configuration ---
# Track scan requests per IP to prevent abuse
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW_SECS', 60))  # Time window in seconds
MAX_SCANS_PER_WINDOW = int(os.environ.get('MAX_SCANS_PER_WINDOW', 5))  # Max scans per window
scan_history = defaultdict(list)  # IP -> [timestamp1, timestamp2, ...]

def check_rate_limit(ip_address):
    """
    Check if the IP has exceeded the rate limit.
    Returns (allowed: bool, retry_after: int|None)
    """
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    # Clean up old entries for this IP
    scan_history[ip_address] = [ts for ts in scan_history[ip_address] if ts > cutoff]

    # Check if limit exceeded
    if len(scan_history[ip_address]) >= MAX_SCANS_PER_WINDOW:
        oldest = scan_history[ip_address][0]
        retry_after = int((oldest + timedelta(seconds=RATE_LIMIT_WINDOW) - now).total_seconds())
        return False, retry_after

    # Record this request
    scan_history[ip_address].append(now)
    return True, None

# --- API Key Authentication ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY') or request.args.get('api_key') # Check header then query param
        if not api_key or api_key != FLASK_API_KEY:
            app.logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify(error="Invalid or missing API key"), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Hybrid Authentication (API Key OR Session) ---
def require_auth(f):
    """Accepts either API key (for external/Laravel calls) or session (for browser/Flask UI)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session
        if session.get('logged_in'):
            return f(*args, **kwargs)

        # Otherwise, check for API key
        api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')
        if api_key and api_key == FLASK_API_KEY:
            return f(*args, **kwargs)

        # No valid authentication found
        app.logger.warning(f"Unauthorized API access attempt from {request.remote_addr}")
        return jsonify(error="Authentication required. Provide valid API key or login."), 401
    return decorated_function

# --- CSV Path ---
CSV_PATH = os.path.join(os.path.dirname(__file__), 'mqtt_scan_report.csv')

# --- Simple User Authentication (Session-based) ---
# WARNING: Store credentials securely in production (e.g., hashed in DB, env vars)
VALID_USERS = {'admin': os.environ.get('FLASK_ADMIN_PASS', 'adminpass')} # Load pass from env or use default

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple comparison (replace with hash check in production)
        if username in VALID_USERS and VALID_USERS[username] == password:
            session['logged_in'] = True
            session['user'] = username
            app.logger.info(f"User '{username}' logged in successfully.")
            next_url = request.args.get('next') or url_for('home')
            return redirect(next_url)
        else:
            error = 'Invalid credentials. Please try again.'
            app.logger.warning(f"Failed login attempt for user '{username}' from {request.remote_addr}")
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    user = session.get('user', 'Unknown')
    session.clear()
    app.logger.info(f"User '{user}' logged out.")
    return redirect(url_for('login'))

# --- UI Route ---
@app.route('/')
@login_required
def home():
    # Render the pretty dashboard template
    return render_template('dashboard_pretty.html')

# --- Helper: Get TLS Certificate Info ---
def get_cert_info(host, port, timeout=3):
    """Fetches and parses the server's TLS certificate into human-readable fields."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE # Accept self-signed for scanning purposes

    cert_info = {
        'subject': None,
        'issuer': None,
        'valid_from': None,
        'valid_to': None,
        'serial_number': None,
        'version': None,
        'pem_snippet': None,
        'error': None
    }

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                # Get certificate in both formats
                cert_dict = ssock.getpeercert()  # Human-readable dict
                der_cert = ssock.getpeercert(binary_form=True)  # Binary for PEM conversion

                if cert_dict:
                    # Extract human-readable fields
                    cert_info['subject'] = dict(x[0] for x in cert_dict.get('subject', []))
                    cert_info['issuer'] = dict(x[0] for x in cert_dict.get('issuer', []))
                    cert_info['valid_from'] = cert_dict.get('notBefore')
                    cert_info['valid_to'] = cert_dict.get('notAfter')
                    cert_info['serial_number'] = cert_dict.get('serialNumber')
                    cert_info['version'] = cert_dict.get('version')

                if der_cert:
                    pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
                    # Store truncated PEM for reference (first 500 chars)
                    cert_info['pem_snippet'] = pem_cert[:500].strip()

    except ssl.SSLError as e:
        cert_info['error'] = f'SSL error: {str(e)}'
    except socket.timeout:
        cert_info['error'] = 'Timeout getting certificate'
    except ConnectionRefusedError:
        cert_info['error'] = 'Connection refused'
    except Exception as e:
        cert_info['error'] = f'Error: {str(e)}'

    return cert_info

# --- Helper: Probe Broker Topics (Enhanced) ---
def probe_broker_topics(host, port, creds=None, use_tls=False, listen_secs=3, capture_all=True):
    """
    Connects and subscribes to capture broker info and active topics.

    Args:
        capture_all: If True, subscribes to # (all topics) to detect publishers.
                     If False, only subscribes to $SYS/# for broker info.
    """
    info = {
        'sys_topics': {},
        'regular_topics': {},
        'retained_topics': [],
        'error': None,
        'sys_count': 0,
        'regular_count': 0,
        'client_list': []
    }
    client = None
    msgs = [] # Collect messages here

    def on_connect(c, userdata, flags, rc, properties=None):
        if rc == 0:
            try:
                # Subscribe based on mode
                if capture_all:
                    c.subscribe("#", qos=0)  # All topics
                    app.logger.debug(f"Subscribed to # (all topics) on {host}:{port}")
                else:
                    c.subscribe("$SYS/#", qos=0)  # Only system topics
                    app.logger.debug(f"Subscribed to $SYS/# on {host}:{port}")
            except Exception as sub_e:
                info['error'] = f"Subscription error: {sub_e}"
                app.logger.error(f"Failed to subscribe on {host}:{port}: {sub_e}")
        else:
            info['error'] = f"Connection failed (rc={rc})"
            app.logger.warning(f"Failed to connect to {host}:{port} for topic probe (rc={rc})")

    def on_message(c, userdata, msg):
        try:
            topic = msg.topic
            # Decode payload safely, handle potential non-UTF8 data
            payload = msg.payload.decode('utf-8', errors='replace')
            is_retained = msg.retain
            msgs.append((topic, payload, is_retained))

            if topic.startswith('$SYS/'):
                info['sys_count'] += 1
            else:
                info['regular_count'] += 1

        except Exception as msg_e:
            app.logger.error(f"Error processing message from {host}:{port} on topic {msg.topic}: {msg_e}")

    try:
        client_id = f"sysprobe-{int(time.time())}"
        # Handle both paho-mqtt v1.x and v2.x compatibility
        try:
            # Try paho-mqtt 2.x style first
            client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
        except (AttributeError, TypeError):
            # Fall back to paho-mqtt 1.x style
            client = mqtt_client.Client(client_id=client_id)

        if creds and creds.get('user'):
            client.username_pw_set(creds.get('user'), creds.get('pass'))

        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try: client.tls_set_context(ctx)
            except Exception:
                try:
                    client.tls_set()
                    client.tls_insecure_set(True)
                except Exception as tls_e:
                    info['error'] = f"TLS setup error: {tls_e}"
                    app.logger.error(f"TLS setup failed for $SYS probe on {host}:{port}: {tls_e}")
                    return info # Cannot proceed without TLS setup

        client.on_connect = on_connect
        client.on_message = on_message

        # Use connect_async for non-blocking connection attempt
        client.connect_async(host, port, keepalive=10)
        client.loop_start()

        # Wait briefly for connection and initial messages
        connect_wait_start = time.time()
        while time.time() - connect_wait_start < listen_secs + 1: # Wait a bit longer than listen_secs
             if info['error'] and 'Connection failed' in info['error']:
                 break # Stop waiting if connection failed early
             time.sleep(0.1)

        client.loop_stop()
        try: client.disconnect()
        except: pass

        # Process collected messages
        for topic, payload, is_retained in msgs:
            # Limit payload length shown for brevity
            payload_snippet = payload[:100] + ('...' if len(payload) > 100 else '')

            # Track retained messages (these show up immediately, indicating existing publishers)
            if is_retained and topic not in [t['topic'] for t in info['retained_topics']]:
                info['retained_topics'].append({'topic': topic, 'payload': payload_snippet})

            # Separate $SYS topics from regular topics
            if topic.startswith('$SYS/'):
                # Extract client list if available
                if 'clients' in topic.lower() or 'connected' in topic.lower():
                    try:
                        # Some brokers publish client lists in $SYS topics
                        if payload.strip():
                            info['client_list'].append({'sys_topic': topic, 'info': payload_snippet})
                    except: pass

                # Store $SYS topics
                if topic not in info['sys_topics']:
                    info['sys_topics'][topic] = payload_snippet
                elif info['sys_topics'][topic] != payload_snippet:
                    # Handle duplicate topics with different payloads
                    if not isinstance(info['sys_topics'][topic], list):
                        info['sys_topics'][topic] = [info['sys_topics'][topic]]
                    if payload_snippet not in info['sys_topics'][topic]:
                        info['sys_topics'][topic].append(payload_snippet)
            else:
                # Store regular topics (non-$SYS)
                if topic not in info['regular_topics']:
                    info['regular_topics'][topic] = {
                        'payload': payload_snippet,
                        'retained': is_retained,
                        'count': 1
                    }
                else:
                    info['regular_topics'][topic]['count'] += 1
                    # Update payload if different
                    if info['regular_topics'][topic]['payload'] != payload_snippet:
                        info['regular_topics'][topic]['last_payload'] = payload_snippet

    except Exception as e:
        info['error'] = f"Probe execution error: {str(e)}"
        app.logger.error(f"Error during $SYS probe for {host}:{port}: {e}")
    finally:
        try: # Ensure cleanup even if errors occurred
            if client:
                client.loop_stop()
                client.disconnect()
        except: pass

    # Clean up error message if successful messages were received
    total_count = info['sys_count'] + info['regular_count']
    if total_count > 0 and info['error'] and 'Connection failed' not in info['error'] and 'Subscription error' not in info['error']:
        info['error'] = None # Clear minor errors if we got data

    return info

# --- API: Run Scan (POST) ---
@app.route('/api/scan', methods=['POST'])
@require_auth
def api_scan():
    # Check rate limit first
    client_ip = request.remote_addr
    allowed, retry_after = check_rate_limit(client_ip)

    if not allowed:
        app.logger.warning(f"Rate limit exceeded for {client_ip}. Retry after {retry_after}s")
        return jsonify({
            'error': 'Rate limit exceeded. Too many scan requests.',
            'retry_after': retry_after,
            'limit': f'{MAX_SCANS_PER_WINDOW} scans per {RATE_LIMIT_WINDOW} seconds'
        }), 429

    start_time = time.time()
    data = request.json or {}
    target = data.get('target', '127.0.0.1') # Default to localhost if no target specified
    creds = data.get('creds') # Optional: {'user': 'x', 'pass': 'y'}

    # Configurable scan parameters with safe defaults
    listen_duration = min(int(data.get('listen_duration', 3)), 10)  # Max 10 seconds
    capture_all_topics = data.get('capture_all_topics', False)  # Default: only $SYS

    app.logger.info(f"Scan request received for target: {target} from {client_ip} (listen={listen_duration}s, capture_all={capture_all_topics})")

    try:
        # run_scan now returns list including 'publishers'
        results = run_scan(target, creds)
        app.logger.info(f"Scan function completed. Found {len(results)} potential results.")

        enriched_results = []
        for r in results:
            # Skip results indicating the port was closed at TCP level initially
            if r.get('classification') == 'closed_or_unreachable':
                 enriched_results.append(r) # Keep record of closed ports
                 continue

            r2 = r.copy() # Work with a copy
            host = r2.get('ip')
            port = r2.get('port')

            if not host or not port:
                app.logger.warning(f"Skipping result with missing host/port: {r}")
                continue

            try: port = int(port) # Ensure port is integer
            except ValueError:
                app.logger.warning(f"Skipping result with invalid port: {r}")
                continue

            is_tls_port = (port == 8883)
            r2['tls'] = is_tls_port # Indicate if it's the standard TLS port

            # Attempt to get Certificate Info for TLS ports
            if is_tls_port:
                app.logger.debug(f"Getting certificate info for {host}:{port}")
                cert_info = get_cert_info(host, port)
                r2['cert_info'] = cert_info
            else:
                r2['cert_info'] = {'error': 'Not a TLS port'}

            # Attempt topic probe if connection was successful
            if r2.get('classification') == 'open_or_auth_ok':
                app.logger.debug(f"Probing broker topics for {host}:{port} (capture_all={capture_all_topics})")
                broker_info = probe_broker_topics(
                    host, port,
                    creds=creds,
                    use_tls=is_tls_port,
                    listen_secs=listen_duration,
                    capture_all=capture_all_topics
                )
                r2['broker_info'] = broker_info

            # Ensure 'publishers' key exists, even if empty
            if 'publishers' not in r2:
                r2['publishers'] = []

            enriched_results.append(r2)

        app.logger.info(f"Enrichment complete for {len(enriched_results)} results.")

        # --- Write results to CSV ---
        if enriched_results: # Only write if there are results
            # Define headers with enhanced certificate and broker info fields
            fieldnames = [
                'ip', 'port', 'result', 'classification', 'tls',
                'cert_subject', 'cert_issuer', 'cert_valid_from', 'cert_valid_to',
                'broker_error', 'sys_topic_count', 'regular_topic_count', 'retained_count',
                'publishers', 'timestamp'
            ]
            try:
                with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    for row in enriched_results:
                        # Extract cert info
                        cert_info = row.get('cert_info', {})
                        cert_subject = json.dumps(cert_info.get('subject')) if cert_info.get('subject') else cert_info.get('error', '')
                        cert_issuer = json.dumps(cert_info.get('issuer')) if cert_info.get('issuer') else ''

                        # Extract broker info
                        broker_info = row.get('broker_info', {})

                        # Prepare row for CSV writing
                        csv_row = {
                            'ip': row.get('ip'),
                            'port': row.get('port'),
                            'result': row.get('result'),
                            'classification': row.get('classification'),
                            'tls': row.get('tls'),
                            'cert_subject': cert_subject,
                            'cert_issuer': cert_issuer,
                            'cert_valid_from': cert_info.get('valid_from', ''),
                            'cert_valid_to': cert_info.get('valid_to', ''),
                            'broker_error': broker_info.get('error', ''),
                            'sys_topic_count': broker_info.get('sys_count', 0),
                            'regular_topic_count': broker_info.get('regular_count', 0),
                            'retained_count': len(broker_info.get('retained_topics', [])),
                            # Serialize publishers list as a JSON string for CSV
                            'publishers': json.dumps(row.get('publishers', [])),
                            'timestamp': row.get('timestamp')
                        }
                        writer.writerow(csv_row)
                app.logger.info(f"Results successfully written to {CSV_PATH}")
            except IOError as e:
                app.logger.error(f"Failed to write CSV file at {CSV_PATH}: {e}")
            except Exception as e:
                 app.logger.error(f"An unexpected error occurred during CSV writing: {e}")
        else:
             app.logger.info("No results to write to CSV.")
             # Optionally clear the CSV or leave it as is from previous scan
             if os.path.exists(CSV_PATH):
                 try: os.remove(CSV_PATH) # Clear old results if scan yields nothing
                 except OSError as e: app.logger.error(f"Could not remove old CSV {CSV_PATH}: {e}")

        elapsed_time = time.time() - start_time
        app.logger.info(f"Scan and processing for target '{target}' completed in {elapsed_time:.2f} seconds.")

        return jsonify({'status':'ok', 'results': enriched_results})

    except Exception as e:
        elapsed_time = time.time() - start_time
        app.logger.error(f"Scan request failed for target '{target}' after {elapsed_time:.2f} seconds: {e}", exc_info=True) # Log full traceback
        return jsonify(error=f"Scan failed: {str(e)}"), 500

# --- API: Get Results (GET) ---
@app.route('/api/results', methods=['GET'])
@require_auth
def api_results():
    """Reads the latest scan results from the CSV file."""
    results = []
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse JSON fields
                    try:
                        row['publishers'] = json.loads(row.get('publishers', '[]'))
                    except json.JSONDecodeError:
                        row['publishers'] = []

                    # Parse certificate subject/issuer if they're JSON strings
                    for cert_field in ['cert_subject', 'cert_issuer']:
                        if row.get(cert_field) and row[cert_field].startswith('{'):
                            try:
                                row[cert_field] = json.loads(row[cert_field])
                            except json.JSONDecodeError:
                                pass  # Keep as string

                    # Convert boolean strings back to boolean
                    row['tls'] = row.get('tls', 'False').lower() == 'true'

                    # Convert count fields back to int
                    for count_field in ['sys_topic_count', 'regular_topic_count', 'retained_count']:
                        try:
                            row[count_field] = int(row.get(count_field, 0))
                        except (ValueError, TypeError):
                            row[count_field] = 0

                    results.append(row)
            app.logger.debug(f"Retrieved {len(results)} results from {CSV_PATH}")
        except IOError as e:
             app.logger.error(f"Failed to read CSV file at {CSV_PATH}: {e}")
             return jsonify(error=f"Could not read results file: {e}"), 500
        except Exception as e:
             app.logger.error(f"An unexpected error occurred reading CSV: {e}")
             return jsonify(error=f"Error processing results file: {e}"), 500
    else:
         app.logger.info(f"Results file not found: {CSV_PATH}")
         # Return empty list, not an error, if file doesn't exist yet
    return jsonify(results)

# --- Main Execution ---
if __name__ == '__main__':
    # Set logging level (e.g., INFO for production, DEBUG for development)
    log_level = os.environ.get('FLASK_LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(log_level)
    app.logger.info(f"Flask app starting with log level {log_level}")

    # Use environment variables for host and port if needed
    host = os.environ.get('FLASK_HOST', '0.0.0.0') # Listen on all interfaces by default
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    app.logger.info(f"Running Flask server on {host}:{port} (Debug: {debug_mode})")
    app.run(host=host, port=port, debug=debug_mode)