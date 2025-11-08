import jwt
import time


JWT_SECRET_KEY = "makeuc-is-awesome-I-love-Berea-2025"

# --- Device 1: Heart Monitor (High Trust) ---
payload_heart_monitor = {
    "device_id": "HM-123",
    "role": "vitals_critical",  # This is the "permission slip"
    "iat": int(time.time()),   # Issued at time
    "exp": int(time.time()) + (24 * 60 * 60) # Expires in 24 hours
}

# --- Device 2: Patient TV (Low Trust) ---
payload_patient_tv = {
    "device_id": "TV-789",
    "role": "media_guest",     # This device has a different, less-privileged role
    "iat": int(time.time()),
    "exp": int(time.time()) + (24 * 60 * 60)
}

# --- Generate the tokens ---
token_heart_monitor = jwt.encode(payload_heart_monitor, JWT_SECRET_KEY, algorithm="HS256")
token_patient_tv = jwt.encode(payload_patient_tv, JWT_SECRET_KEY, algorithm="HS256")

print("--- SHARE THESE TOKENS WITH YOUR TEAM (Role 4) ---")
print("\nTOKEN_HEART_MONITOR (Role: vitals_critical):")
print(token_heart_monitor)
print("\nTOKEN_PATIENT_TV (Role: media_guest):")
print(token_patient_tv)