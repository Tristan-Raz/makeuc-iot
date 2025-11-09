import requests
import json

# --- Auth0 M2M Client Configuration ---
# These values are from your PowerShell logs.
# This represents your "Heart Monitor" device.
AUTH0_DOMAIN = "dev-4a45sa8f3kkwulii.us.auth0.com"
CLIENT_ID = "R07D0IFkbljDwxYNSIYvEdxA5yB6LuA4"
CLIENT_SECRET = "_dAvbokb5zzPjur3RavkIYbxHeKj-FLG1m4OqhCOspnx-xjqUtItmLNRHtq53NIk"
AUDIENCE = "https://uc-iot.tech/api"  # The API you are protecting


def get_auth0_token():
    """
    Requests an Access Token from Auth0 using the Client Credentials flow.
    This is the M2M (device-to-service) equivalent of logging in.
    """
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "client_credentials"
    }

    try:
        # Use the 'json' parameter for robustness
        response = requests.post(token_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        token_data = response.json()

        if "access_token" in token_data:
            access_token = token_data['access_token']

            # --- 1. Print to console (will likely be truncated) ---
            print("--- Auth0 Access Token (Role: Heart Monitor) ---")
            print(f"Token (display): {access_token}")

            # --- 2. Save full token to a file ---
            with open("token.txt", "w") as f:
                f.write(access_token)

            print("\n*** FULL TOKEN SAVED TO token.txt ***")
            print("Open that file to get the complete token.")
            return access_token
        else:
            print("--- Error: 'access_token' not in response ---")
            print(f"Response: {token_data}")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"--- HTTP Error: {e.response.status_code} ---")
        print(f"Response Body: {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    get_auth0_token()