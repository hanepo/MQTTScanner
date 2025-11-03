import requests
import json

headers = {'X-API-KEY': 'my-very-secret-flask-key-CHANGEME'}
r = requests.get('http://127.0.0.1:5000/api/scan/scan-ba562d58/results', headers=headers)
data = r.json()

print(f"Total results: {data.get('count')}\n")

for result in data.get('results', []):
    port = result.get('port')
    print(f"=== Port {port} ===")
    
    publishers = result.get('publishers', [])
    print(f"Total publishers: {len(publishers)}")
    
    # Find sensor topics
    sensor_topics = [p for p in publishers if 'dht11' in p.get('topic', '') or 'multi' in p.get('topic', '') or 'sensors/hanif' in p.get('topic', '')]
    
    if sensor_topics:
        print(f"Sensor topics found: {len(sensor_topics)}")
        for pub in sensor_topics:
            topic = pub.get('topic')
            payload = pub.get('payload_sample', '')
            print(f"  - {topic}")
            print(f"    Payload: {payload[:100]}...")
    else:
        print("No sensor topics found")
    print()
