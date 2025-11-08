import requests, sys, time

if len(sys.argv) < 2:
    print("Usage: python attacker_simulator.py <GATEWAY_URL>")
    sys.exit(1)

GATEWAY = sys.argv[1].rstrip("/")
FAKE_TOKEN = "this.is.not.a.real.jwt"
headers = {"Authorization": f"Bearer {FAKE_TOKEN}", "Content-Type": "application/json"}

def spoof():
    payload = {"device_id": "HM-123", "data": {"bpm": 9999}, "ts": time.time()}
    try:
        r = requests.post(GATEWAY, json=payload, headers=headers, timeout=5)
        print(time.strftime("%X"), "ATTACK ->", r.status_code, r.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    while True:
        spoof()
        time.sleep(1)

