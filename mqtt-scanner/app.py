# app.py — prettier Flask UI + auth + TLS info + $SYS probe
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from scanner import run_scan
import csv, os, ssl, socket, time
from functools import wraps
from paho.mqtt import client as mqtt_client

app = Flask(__name__, template_folder='templates')
app.secret_key = 'replace-this-with-a-strong-random-secret'  # change in production
CORS(app)

# read secret API key from env (default for dev)
FLASK_API_KEY = os.environ.get('FLASK_API_KEY', 'my-very-secret-flask-key-CHANGEME')

def require_api_key(fn):
    def wrapper(*args, **kwargs):
        api_key = None
        # check header first
        if 'X-API-KEY' in request.headers:
            api_key = request.headers.get('X-API-KEY')
        # optionally accept api_key in query for debugging (avoid in prod)
        if not api_key:
            api_key = request.args.get('api_key')
        if not api_key or api_key != FLASK_API_KEY:
            return jsonify({'error': 'invalid api key'}), 401
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


CSV_PATH = os.path.join(os.path.dirname(__file__), 'mqtt_scan_report.csv')

# --- simple auth (session-based). Replace with real auth in prod ---
VALID_USERS = {'admin': 'adminpass'}   # CHANGE THIS. Or load from env/DB.

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get('logged_in') != True:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return wrapped

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u in VALID_USERS and VALID_USERS[u] == p:
            session['logged_in'] = True
            session['user'] = u
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- UI ---
@app.route('/')
@login_required
def home():
    return render_template('dashboard_pretty.html')

# --- helper: get TLS certificate snippet (PEM header info) ---
def get_cert_snippet(host, port, timeout=3):
    try:
        pem = ssl.get_server_certificate((host, port), timeout=timeout)
        # return first 200 chars for brevity
        return pem[:1000].replace('\n', '\\n')
    except Exception as e:
        return f'error: {str(e)}'

# --- helper: probe broker $SYS for client counts / topics (quick) ---
def probe_sys_topics(host, port, creds=None, use_tls=False, listen_secs=2):
    info = {}
    client = None
    try:
        client_id = f"probe-{int(time.time())}"
        client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1)
        if creds:
            client.username_pw_set(creds.get('user'), creds.get('pass'))
        # attach TLS if requested
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                client.tls_set_context(ctx)
            except Exception:
                try:
                    client.tls_set()
                    client.tls_insecure_set(True)
                except Exception:
                    pass

        msgs = []
        def on_message(c, userdata, msg):
            try:
                topic = msg.topic
                payload = msg.payload.decode('utf-8', errors='ignore')
                msgs.append((topic, payload))
            except:
                pass

        client.on_message = on_message
        client.connect(host, port, keepalive=5)
        client.loop_start()
        # subscribe to $SYS/# (many brokers expose runtime info here)
        try:
            client.subscribe("$SYS/#")
        except:
            pass
        t0 = time.time()
        while time.time() - t0 < listen_secs:
            time.sleep(0.1)
        client.loop_stop()
        try: client.disconnect()
        except: pass

        # parse messages for common sys keys
        for t, p in msgs:
            if t.endswith('/clients/count') or 'clients' in t:
                info.setdefault('sys', []).append({t: p})
            else:
                info.setdefault('sys', []).append({t: p})
        info['raw_count'] = len(msgs)
    except Exception as e:
        info['error'] = str(e)
    finally:
        try:
            if client:
                client.loop_stop()
                client.disconnect()
        except:
            pass
    return info

# --- API: run scan (POST) ---
@app.route('/api/scan', methods=['POST'])
@require_api_key
def api_scan():
    data = request.json or {}
    target = data.get('target', '127.0.0.1')
    creds = data.get('creds')
    # run_scan returns list of results (ip,port,result,classification,timestamp)
    results = run_scan(target, creds)
    # enrich results with TLS / cert info / $SYS probe for TLS ports
    enriched = []
    for r in results:
        r2 = r.copy()
        host = r2['ip']; port = int(r2['port'])
        is_tls = (port == 8883 or r2['port'] == 8883)
        r2['tls'] = is_tls
        # cert snippet (only for tls port)
        if is_tls:
            r2['cert_snippet'] = get_cert_snippet(host, port)
            # run quick $SYS probe if connected
            if r2.get('classification') == 'open_or_auth_ok':
                r2['broker_sys'] = probe_sys_topics(host, port, creds=creds, use_tls=is_tls)
        enriched.append(r2)

    # write CSV for convenience
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ip','port','result','classification','timestamp'])
        writer.writeheader()
        for row in enriched:
            writer.writerow({'ip':row.get('ip'),'port':row.get('port'),'result':row.get('result'),'classification':row.get('classification'),'timestamp':row.get('timestamp')})
    return jsonify({'status':'ok','results':enriched})

# --- API: results (GET) ---
@app.route('/api/results', methods=['GET'])
@require_api_key
def api_results():
    results = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            results = list(reader)
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
