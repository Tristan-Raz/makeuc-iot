import jwt  # Keep this import for the PyJWTError exception
from jose import jwk, jwt as jose_jwt  # We use 'jose' for RS256 validation
from jose.utils import base64url_decode

import requests  # Need this to fetch the public keys
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
import json  # Used for fetching/caching jwks

# --- CONFIGURATION ---
# These MUST match your simulator script and Auth0 application settings
AUTH0_DOMAIN = "dev-4a45sa8f3kkwulii.us.auth0.com"
AUDIENCE = "https://uc-iot.tech/api"
ALGORITHMS = ["RS256"]  # We are now using RS256

LOG_FILE = "log.txt"  # Define the log file name

app = FastAPI()
token_auth_scheme = HTTPBearer()

# --- Cache for Auth0's Public Keys (JWKS) ---
# We cache this so we don't have to re-fetch it on every single API call
jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks_cache = {}


def get_jwks():
    """
    Fetches and caches the JWKS from Auth0.
    """
    global jwks_cache
    if not jwks_cache:
        try:
            response = requests.get(jwks_url)
            response.raise_for_status()
            jwks_cache = response.json()
        except requests.exceptions.RequestException as e:
            print(f"!!! CRITICAL: FAILED TO FETCH JWKS: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch authentication keys.")
    return jwks_cache


# --- Helper Function to write to the log ---
def write_to_log(device_id: str, role: str, target: str, status: str, detail: str):
    """
    Writes a standardized log entry to the log.txt file.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    log_entry = f"{timestamp},{device_id},{role},{target},{status},{detail}\n"

    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"!!! CRITICAL: FAILED TO WRITE TO LOG FILE: {e}")


# --- THE "BRAIN'S" HELPER: REBUILT TOKEN DECODER ---
def get_validated_payload(token: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_str = token.credentials

    try:
        # 1. Get the JWKS (public keys) from Auth0
        jwks = get_jwks()

        # 2. Get the 'kid' (Key ID) from the unverified token header
        unverified_header = jose_jwt.get_unverified_header(token_str)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if not rsa_key:
            print("!!! AUTH ATTEMPT FAILED: Unable to find matching public key (kid).")
            raise credentials_exception

        # 3. Decode and validate the token using the correct public key
        payload = jose_jwt.decode(
            token_str,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload

    except jose_jwt.ExpiredSignatureError:
        print("!!! AUTH ATTEMPT FAILED: Token is expired.")
        raise credentials_exception
    except jose_jwt.JWTClaimsError:
        print("!!! AUTH ATTEMPT FAILED: Invalid claims (e.g., audience or issuer).")
        raise credentials_exception
    except (jose_jwt.JWTError, jwt.PyJWTError, Exception) as e:
        # This catches malformed tokens, invalid signatures, etc.
        print(f"!!! SPOOFING ATTEMPT DETECTED (or invalid token): {e}")

        # --- LOGGING THE ATTACK (Token is malformed or invalid signature) ---
        write_to_log(
            device_id="Unknown",
            role="Unknown",
            target="Unknown",  # Don't know the target yet
            status="DENIED_SPOOFING",
            detail=str(e)
        )
        raise credentials_exception


# --- ENDPOINT 1: THE CRITICAL ZERO TRUST ENDPOINT (/vitals-db) ---
@app.post("/vitals-db")
async def write_vitals(request: Request, payload: dict = Depends(get_validated_payload)):
    # FIX: The 'gzt' (guest) scope from Auth0 is now in 'permissions'
    # We will get the role from the client_id or metadata later.
    # For this hackathon, let's use 'gzt' (permissions) as the role.

    permissions = payload.get("permissions", [])
    device_id = payload.get("azp", "Unknown")  # azp = Authorized Party (Client ID)
    target_endpoint = "/vitals-db"

    # --- THE ZERO TRUST POLICY (Only 'write:vitals' permission allowed) ---
    if "write:vitals" in permissions:
        # --- LOGGING THE SUCCESS ---
        print(f"ACCESS GRANTED: Device '{device_id}' (Permissions: {permissions}) accessed {target_endpoint}")
        write_to_log(device_id, str(permissions), target_endpoint, "GRANTED", "Access permitted by policy")
        return {"status": "ACCESS_GRANTED", "device": device_id, "detail": "Vitals written successfully."}
    else:
        # --- LOGGING THE POLICY VIOLATION ---
        print(f"!!! ACCESS DENIED: Device '{device_id}' (Permissions: {permissions}) tried to access {target_endpoint}")
        write_to_log(device_id, str(permissions), target_endpoint, "DENIED_POLICY", "Permissions not authorized")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Client '{device_id}' does not have 'write:vitals' permission."
        )


# --- ENDPOINT 2: THE LOW-TRUST ENDPOINT (/guest-data) ---
@app.get("/guest-data")
async def read_guest_data(payload: dict = Depends(get_validated_payload)):
    permissions = payload.get("permissions", [])
    device_id = payload.get("azp", "Unknown")
    target_endpoint = "/guest-data"

    # --- THE LOW-TRUST POLICY (Allows 'read:guest_data' permission) ---
    if "read:guest_data" in permissions:
        print(f"ACCESS GRANTED: Device '{device_id}' (Permissions: {permissions}) accessed {target_endpoint}")
        write_to_log(device_id, str(permissions), target_endpoint, "GRANTED", "Low-trust access permitted")

        return {"status": "ACCESS_GRANTED", "device": device_id,
                "data": "Guest Wi-Fi password is 'hospital_guest_2025'"}
    else:
        # --- LOGGING THE POLICY VIOLATION ---
        print(f"!!! ACCESS DENIED: Device '{device_id}' (Permissions: {permissions}) tried to access {target_endpoint}")
        write_to_log(device_id, str(permissions), target_endpoint, "DENIED_POLICY", "Permissions not authorized")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Client '{device_id}' does not have 'read:guest_data' permission."
        )


# --- A simple endpoint to see if the server is alive ---
@app.get("/")
def root():
    return {"message": "Zero Trust Gateway is ALIVE! (v4 with Auth0 RS256 Validation)"}