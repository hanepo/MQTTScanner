# debug_connect.py
import time
import ssl
from paho.mqtt import client as mqtt_client

host = "127.0.0.1"
port = 8883
user = "testuser"
password = "testpass"

def on_connect(client, userdata, flags, rc):
    print("on_connect rc=", rc)

def safe_tls_setup(client):
    """
    Try to attach an SSLContext (preferred). If not supported by this paho
    version, fall back to tls_set() + tls_insecure_set(True).
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        # newer paho supports tls_set_context
        client.tls_set_context(ctx)
    except Exception:
        # fallback for older paho: disable verification (demo only)
        try:
            client.tls_set()              # uses default CAs
            client.tls_insecure_set(True) # accept self-signed
        except Exception as e:
            print("tls fallback error:", e)

def main():
    client = None
    try:
        client = mqtt_client.Client("dbg")   # paho 1.6.1 style
        client.username_pw_set(user, password)
        client.on_connect = on_connect

        # attach TLS in a robust way
        safe_tls_setup(client)

        # blocking connect (per our scanner behavior)
        client.connect(host, port, keepalive=5)
        client.loop_start()
        time.sleep(4)
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass
        print("done")
    except Exception as e:
        print("exception:", e)
    finally:
        # attempt to properly close sockets if paho left anything open
        try:
            if client is not None:
                client.loop_stop()
                client.disconnect()
        except Exception:
            pass

if __name__ == "__main__":
    main()
