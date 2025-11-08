import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- CONFIGURATION ---
# This MUST match the key from your token_generator.py
JWT_SECRET_KEY = "makeuc-is-awesome-but-change-this-secret"

app = FastAPI()
token_auth_scheme = HTTPBearer()


# --- The "Brain's" Helper: Token Decoder ---
def get_validated_payload(token: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    """
    Decodes and validates the JWT token from the "Authorization: Bearer <token>" header.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Get the token string from the credentials
        token_str = token.credentials

        # Decode it! This is the "Spoofing" check.
        # If the token is fake or the signature is bad, it fails here.
        payload = jwt.decode(token_str, JWT_SECRET_KEY, algorithms=["HS256"])

        return payload

    except jwt.PyJWTError:
        # This catches "InvalidTokenError", "ExpiredSignatureError", etc.
        # We don't trust it.
        print("!!! SPOOFING ATTEMPT DETECTED (or invalid token) !!!")
        raise credentials_exception
    except Exception as e:
        print(f"!!! An unknown error occurred: {e}")
        raise credentials_exception


# --- THE ZERO TRUST ENDPOINT ---
@app.post("/vitals-db")
async def check_vitals_access(request: Request, payload: dict = Depends(get_validated_payload)):
    """
    This endpoint represents the high-security Vitals Database.
    It's protected by our Zero Trust policy.
    """

    # We get the payload *after* it's been validated by get_validated_payload
    device_role = payload.get("role")
    device_id = payload.get("device_id")

    # --- THE ZERO TRUST POLICY ---
    # This is the core logic.
    if device_role == "vitals_critical":
        # Policy PASSED. This device is allowed.
        print(f"ACCESS GRANTED: Device '{device_id}' (Role: {device_role}) accessed /vitals-db")
        return {"status": "ACCESS_GRANTED", "device": device_id}
    else:
        # Policy FAILED. This device is NOT allowed.
        print(f"!!! ACCESS DENIED: Device '{device_id}' (Role: {device_role}) tried to access /vitals-db")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Device role '{device_role}' is not authorized for this resource."
        )


# --- A simple endpoint to see if the server is alive ---
@app.get("/")
def root():
    return {"message": "Zero Trust Gateway is ALIVE!"}