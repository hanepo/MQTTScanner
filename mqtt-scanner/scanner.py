import ssl
import socket, time, datetime
from paho.mqtt import client as mqtt_client

COMMON_PORTS = [1883, 8883]
TIMEOUT = 2

def try_mqtt_connect(host, port, use_tls=False, username=None, password=None, wait_secs=6):
    result = {'ip':host, 'port':port, 'result':'unknown', 'classification':'unknown', 'timestamp': datetime.datetime.utcnow().isoformat()}
    client = None
    try:
        client_id = f"scanner-{int(time.time())}"
        client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1)
        if username:
            client.username_pw_set(username, password)

        # robust TLS attach (works with both older and newer paho)
        if use_tls:
            # create an unverified context for demo (accept self-signed certs)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                client.tls_set_context(ctx)   # preferred
            except Exception:
                try:
                    client.tls_set()
                    client.tls_insecure_set(True)
                except Exception:
                    pass

        connected = False
        last_rc = None

        def on_connect(c, userdata, flags, rc):
            nonlocal connected, last_rc
            last_rc = rc
            connected = (rc == 0)

        client.on_connect = on_connect

        # blocking connect so TLS handshake + auth complete during connect()
        client.connect(host, port, keepalive=5)
        client.loop_start()
        timeout = time.time() + wait_secs
        while time.time() < timeout and not connected:
            time.sleep(0.1)
        client.loop_stop()
        try:
            client.disconnect()
        except:
            pass

        if connected:
            result['result'] = 'connected'
            result['classification'] = 'open_or_auth_ok'
        else:
            result['result'] = 'connect_failed'
            if last_rc is not None:
                result['result'] += f' (rc={last_rc})'
                result['classification'] = 'not_authorized' if last_rc == 5 else 'not_authorized_or_unreachable'
            else:
                result['classification'] = 'not_authorized_or_unreachable'
    except Exception as e:
        result['result'] = f'error:{str(e)}'
        if 'SSL' in str(e) or 'tls' in str(e).lower():
            result['classification'] = 'tls_or_ssl_error'
        else:
            result['classification'] = 'error'
    finally:
        # try to clean up
        try:
            if client is not None:
                client.loop_stop()
                client.disconnect()
        except:
            pass
    return result


def scan_ip(ip, creds=None):
    results = []
    for p in COMMON_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        try:
            s.connect((ip, p))
            s.close()
            is_tls = (p == 8883)
            # First try anonymous (no creds)
            res = try_mqtt_connect(ip, p, use_tls=is_tls, wait_secs=4)
            # If TLS port and anonymous failed, and creds provided, try with credentials
            if is_tls and res['classification'] != 'open_or_auth_ok' and creds:
                res_with_creds = try_mqtt_connect(ip, p, use_tls=is_tls, username=creds.get('user'), password=creds.get('pass'), wait_secs=4)
                # prefer positive result
                if res_with_creds['classification'] == 'open_or_auth_ok':
                    res = res_with_creds
            results.append(res)
        except Exception:
            res = {'ip':ip, 'port':p, 'result':'closed', 'classification':'closed', 'timestamp': datetime.datetime.utcnow().isoformat()}
            results.append(res)
    return results

def run_scan(target, creds=None):
    ips = []
    if '/' in target:
        base = target.split('/')[0]
        parts = base.split('.')
        if target.endswith('/24'):
            prefix = '.'.join(parts[:3])
            ips = [f"{prefix}.{i}" for i in range(1,255)]
        else:
            ips = [base]
    else:
        ips=[target]
    allr=[]
    for ip in ips:
        allr.extend(scan_ip(ip, creds))
    return allr

if __name__ == '__main__':
    print(run_scan('127.0.0.1', creds={'user':'testuser','pass':'testpass'}))
