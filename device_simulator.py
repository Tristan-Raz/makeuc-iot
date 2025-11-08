import requests, sys, time

if len(sys.argv) < 4:
    print("Usage: python device_simulator.py <TOKEN> <GATEWAY_URL> <DEVICE_ID>")
    sys.exit(1)

TOKEN, GATEWAY_URL, DEVICE_ID = sys.argv[1], sys.argv[2].rstrip("/"), sys.argv[3]
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def send_vitals():
    payload = {"device_id": DEVICE_ID, "data": {"bpm": 70, "spo2": 98}, "ts": time.time()}
    try:
        r = requests.post(GATEWAY_URL, json=payload, headers=headers, timeout=5)
        print(time.strftime("%X"), "->", r.status_code, r.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    while True:
        send_vitals()
        time.sleep(2)
