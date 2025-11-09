import requests
import json
import time

# --- Auth0 M2M Client Configuration for LOW TRUST Device (Patient TV) ---
# IMPORTANT: Use DIFFERENT credentials for a different application created in Auth0.
AUTH0_DOMAIN = "YOUR_AUTH0_DOMAIN.us.auth0.com"  # Should be the same as the high-trust client
LOW_TRUST_CLIENT_ID = "YOUR_PATIENT_TV_CLIENT_ID"  # <-- New ID for the Low Trust App (Must be filled in)
LOW_TRUST_CLIENT_SECRET = "YOUR_PATIENT_TV_CLIENT_SECRET"  # <-- New Secret for the Low Trust App (Must be filled in)
AUDIENCE = "https://uc-iot.tech/api"


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
        print(f"Response: {response.text}")
        return None
    except Exception as e:
        print(f"!!! An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    print(f"Requesting LOW TRUST Token from Auth0 for Client ID: {LOW_TRUST_CLIENT_ID}...")
    token = get_auth0_token(LOW_TRUST_CLIENT_ID, LOW_TRUST_CLIENT_SECRET)

    if token:
        filename = "token_low_trust.txt"
        with open(filename, "w") as f:
            f.write(token)
        print(f"*** FULL LOW-TRUST TOKEN SAVED TO {filename} ***")
    else:
        print("Failed to retrieve token. Check your CLIENT_ID/SECRET and network.")