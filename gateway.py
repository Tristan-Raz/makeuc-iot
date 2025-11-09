import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time

# --- CONFIGURATION ---
# This MUST match the key from your token_generator.py
JWT_SECRET_KEY = "makeuc-is-awesome-I-love-Berea-2025"
LOG_FILE = "log.txt"  # Define the log file name

app = FastAPI()
token_auth_scheme = HTTPBearer()


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


# --- The "Brain's" Helper: Token Decoder ---
def get_validated_payload(token: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_str = token.credentials
        # The key difference: using the local symmetric key for validation
        # FIX: Added leeway=10 to tolerate minor clock skew on timestamps
        payload = jwt.decode(token_str, JWT_SECRET_KEY, algorithms=["HS256"], leeway=10)
        return payload

    except jwt.PyJWTError as e:
        # --- LOGGING THE ATTACK (Token is malformed or invalid signature) ---
        print("!!! SPOOFING ATTEMPT DETECTED (or invalid token) !!!")

        write_to_log(
            device_id="Unknown",
            role="Unknown",
            target="/vitals-db",
            status="DENIED_SPOOFING",
            detail=str(e)
        )
        raise credentials_exception
    except Exception as e:
        print(f"!!! An unknown error occurred: {e}")
        raise credentials_exception


# --- ENDPOINT 1: THE CRITICAL ZERO TRUST ENDPOINT (/vitals-db) ---
@app.post("/vitals-db")
async def write_vitals(request: Request, payload: dict = Depends(get_validated_payload)):
    device_role = payload.get("role", "Unknown")
    device_id = payload.get("device_id", "Unknown")
    target_endpoint = "/vitals-db"

    # --- THE ZERO TRUST POLICY (Only vitals_critical allowed) ---
    if device_role == "vitals_critical":
        # --- LOGGING THE SUCCESS ---
        print(f"ACCESS GRANTED: Device '{device_id}' (Role: {device_role}) accessed {target_endpoint}")
        write_to_log(device_id, device_role, target_endpoint, "GRANTED", "Access permitted by policy")
        return {"status": "ACCESS_GRANTED", "device": device_id, "detail": "Vitals written successfully."}
    else:
        # --- LOGGING THE POLICY VIOLATION ---
        print(f"!!! ACCESS DENIED: Device '{device_id}' (Role: {device_role}) tried to access {target_endpoint}")
        write_to_log(device_id, device_role, target_endpoint, "DENIED_POLICY", "Role not authorized")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device role '{device_role}' is not authorized for this resource."
        )


# --- ENDPOINT 2: THE LOW-TRUST ENDPOINT (/guest-data) ---
@app.get("/guest-data")
async def read_guest_data(payload: dict = Depends(get_validated_payload)):
    device_role = payload.get("role", "Unknown")
    device_id = payload.get("device_id", "Unknown")
    target_endpoint = "/guest-data"

    # --- THE LOW-TRUST POLICY (Allows any authenticated device to read guest data) ---
    # Since the policy is minimal, any valid token will pass the security step above.

    print(f"ACCESS GRANTED: Device '{device_id}' (Role: {device_role}) accessed {target_endpoint}")
    write_to_log(device_id, device_role, target_endpoint, "GRANTED", "Low-trust access permitted")

    return {"status": "ACCESS_GRANTED", "device": device_id, "data": "Guest Wi-Fi password is 'hospital_guest_2025'"}


# --- A simple endpoint to see if the server is alive ---
@app.get("/")
def root():
    return {"message": "Zero Trust Gateway is ALIVE! (v3 with Full Scenarios)"}