import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
import requests
#from jose import jwk
#from jose.utils import base64url_decode

# --- CONFIGURATION ---
# IMPORTANT: Replace this placeholder with YOUR actual Auth0 domain.
# It must match the domain used to create the Client ID in token_requester.py.
AUTH0_DOMAIN = "dev-4a45sa8f3kkwulii.us.auth0.com"
API_AUDIENCE = "https://uc-iot.tech/api"  # This is your API identifier
ALGORITHMS = ["RS256"]  # Auth0 uses RS256
LOG_FILE = "log.txt"

app = FastAPI()
token_auth_scheme = HTTPBearer()

# --- Fetch Auth0 Public Keys (JWKS) ---
# We do this once at startup
try:
    if "YOUR_AUTH0_DOMAIN" in AUTH0_DOMAIN:
        raise Exception("AUTH0_DOMAIN placeholder not replaced.")

    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks_response = requests.get(jwks_url)
    jwks_response.raise_for_status()
    jwks = jwks_response.json()
    print("Successfully fetched JWKS from Auth0.")
except Exception as e:
    print(f"!!! CRITICAL: FAILED TO FETCH JWKS. Server cannot validate tokens. Error: {e}")
    jwks = {}  # Server will fail all requests, which is secure.


# --- Helper Function to write to the log (Unchanged) ---
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


# --- Auth0 Token Validator ---
def get_validated_payload(token: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    """
    Decodes and validates the Auth0 Access Token (JWT).
    It uses the Auth0 public key (JWKS) to verify the signature.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_str = token.credentials

    try:
        # Get the unverified header from the token
        unverified_header = jwt.get_unverified_header(token_str)
    except jwt.PyJWTError as e:
        # This is a good place to log a malformed token
        write_to_log("Unknown", "Unknown", "/vitals-db", "DENIED_SPOOFING", f"Malformed token: {e}")
        raise credentials_exception

    if "kid" not in unverified_header:
        write_to_log("Unknown", "Unknown", "/vitals-db", "DENIED_SPOOFING", "Missing 'kid' in token header")
        raise credentials_exception

    kid = unverified_header["kid"]
    rsa_key = {}

    # Find the matching key in the JWKS
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break

    if not rsa_key:
        write_to_log("Unknown", "Unknown", "/vitals-db", "DENIED_SPOOFING",
                     "Unknown 'kid'. Possible key rotation or spoof.")
        raise credentials_exception

    # --- Perform the validation ---
    try:
        payload = jwt.decode(
            token_str,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload

    except jwt.ExpiredSignatureError:
        write_to_log("Unknown", "Unknown", "/vitals-db", "DENIED_SPOOFING", "Token is expired")
        raise credentials_exception
    except jwt.InvalidAudienceError:
        write_to_log("Unknown", "Unknown", "/vitals-db", "DENIED_SPOOFING",
                     "Incorrect audience (token not for this API)")
        raise credentials_exception
    except jwt.PyJWTError as e:
        write_to_log("Unknown", "Unknown", "/vitals-db", "DENIED_SPOOFING", f"Token validation error: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"!!! An unknown error occurred during token decoding: {e}")
        raise credentials_exception


# --- THE ZERO TRUST ENDPOINT ---
@app.post("/vitals-db")
async def check_vitals_access(request: Request, payload: dict = Depends(get_validated_payload)):
    # In M2M, the "subject" (sub) or "authorized party" (azp) is the Client ID
    device_id = payload.get("azp", payload.get("sub", "Unknown"))

    # --- IMPORTANT: We now check "permissions" instead of "role" ---
    # Auth0 puts permissions in a list called `permissions`
    permissions = payload.get("permissions", [])
    target_endpoint = "/vitals-db"

    # --- THE NEW ZERO TRUST POLICY ---
    # We check for a specific permission, not a role.
    if "access:vitals_critical" in permissions:
        # --- LOGGING THE SUCCESS ---
        print(f"ACCESS GRANTED: Device '{device_id}' (Permissions: {permissions}) accessed {target_endpoint}")
        write_to_log(device_id, "N/A", target_endpoint, "GRANTED",
                     "Access permitted by policy (has 'access:vitals_critical')")
        # --- END OF LOGIC ---

        return {"status": "ACCESS_GRANTED", "device": device_id}
    else:
        # --- LOGGING THE POLICY VIOLATION ---
        print(f"!!! ACCESS DENIED: Device '{device_id}' (Permissions: {permissions}) tried to access {target_endpoint}")
        write_to_log(device_id, "N/A", target_endpoint, "DENIED_POLICY",
                     "Permission 'access:vitals_critical' not found")
        # --- END OF LOGIC ---

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device '{device_id}' does not have the required 'access:vitals_critical' permission."
        )


# --- A simple endpoint to see if the server is alive ---
@app.get("/")
def root():
    return {"message": "Auth0 Zero Trust Gateway is ALIVE! (v2 with Logging)"}