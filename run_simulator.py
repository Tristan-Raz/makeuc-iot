import requests
import json
import time
import jwt
import os

# --- CONSOLIDATED CONFIGURATION ---
# IMPORTANT: These placeholders MUST match the values you put in token_requester.py
# and token_requester_low_trust.py
AUTH0_DOMAIN = "dev-4a45sa8f3kkwulii.us.auth0.com"
HIGH_TRUST_CLIENT_ID = "R07D0IFkbljDwxYNSIYvEdxA5yB6LuA4"
HIGH_TRUST_CLIENT_SECRET = "_dAvbokb5zzPjur3RavkIYbxHeKj-FLG1m4OqhCOspnx-xjqUtItmLNRHtq53NIk"
LOW_TRUST_CLIENT_ID = "WqioD4kHeWyD0liLq0Cprgw57cb3sgws"
LOW_TRUST_CLIENT_SECRET = "HP1TvzgevaWfj7YgBCJ5M9HEuEqm54RKckXbICYiNkJDplhYjR3MwW60CA2Q-lbn"
AUDIENCE = "https://uc-iot.tech/api"
API_URL_BASE = "http://127.0.0.1:8000"



# --- Token Generation Function ---
def get_auth0_token(client_id, client_secret):
    """Fetches a token from Auth0 using client_credentials grant."""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": AUDIENCE,
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except requests.exceptions.HTTPError as e:
        print(f"!!! HTTP Error fetching token: {response.status_code}")
        print(f"Auth0 Response: {response.text}")
        return None
    except Exception as e:
        print(f"!!! An unexpected error occurred during token fetch: {e}")
        return None


# --- API Call Function ---
def call_api(token, endpoint, method="POST"):
    """Makes a request to the local FastAPI server."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_URL_BASE}{endpoint}"

    print(f"\n[REQUEST] Attempting to call {endpoint} with token from {token[:4]}...")

    try:
        if method == "POST":
            response = requests.post(url, headers=headers)
        elif method == "GET":
            response = requests.get(url, headers=headers)

        response.raise_for_status()

        # If successful, parse and print the result
        print(f"  [SUCCESS] Status: {response.status_code} OK")
        print(f"  [RESPONSE]: {response.json()}")

    except requests.exceptions.HTTPError as e:
        # If policy denial (403) or unauthorized (401)
        print(f"  [DENIAL] Status: {response.status_code} {response.reason}")
        try:
            print(f"  [DETAIL]: {response.json().get('detail', response.text)}")
        except:
            print(f"  [DETAIL]: {response.text}")


# ----------------------------------------------------
#               SIMULATION SCENARIOS
# ----------------------------------------------------

def run_simulation():
    if "YOUR_AUTH0_DOMAIN" in AUTH0_DOMAIN:
        print("!!! ERROR: Please fill in all YOUR_... placeholders in the simulator script before running. !!!")
        return

    # --- SCENARIO 1: HIGH TRUST SUCCESS (Heart Monitor -> Vitals) ---
    print("\n--- 1. HIGH TRUST: Heart Monitor Accessing Vitals (Expected: GRANT) ---")
    high_trust_token = get_auth0_token(HIGH_TRUST_CLIENT_ID, HIGH_TRUST_CLIENT_SECRET)
    if high_trust_token:
        call_api(high_trust_token, "/vitals-db", method="POST")

    # --- SCENARIO 2: LOW TRUST DENIAL (Patient TV -> Vitals) ---
    print("\n--- 2. LOW TRUST: Patient TV Accessing Vitals (Expected: DENIAL 403) ---")
    low_trust_token = get_auth0_token(LOW_TRUST_CLIENT_ID, LOW_TRUST_CLIENT_SECRET)
    if low_trust_token:
        call_api(low_trust_token, "/vitals-db", method="POST")

    # --- SCENARIO 3: LOW TRUST GRANTS (Patient TV -> Guest Data) ---
    # NOTE: This only works if you granted the Patient TV client the 'read:guest_data' permission in Auth0!
    print("\n--- 3. LOW TRUST: Patient TV Accessing Guest Data (Expected: GRANT 200) ---")
    if low_trust_token:
        call_api(low_trust_token, "/guest-data", method="GET")

    # --- SCENARIO 4: ATTACK SIMULATION (Malformed Token) ---
    print("\n--- 4. ATTACK: Spoofed/Malformed Token (Expected: DENIAL 401) ---")
    malformed_token = "invalid.jwt.token"
    call_api(malformed_token, "/vitals-db", method="POST")

    print("\n*** Simulation Complete. Check auth0_server.py log (Terminal 1) for full denial details. ***")


if __name__ == "__main__":
    run_simulation()