import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess
import sys
from pathlib import Path

# ---- Configs ----
GATEWAY_URL = "http://127.0.0.1:8000/vitals-db"
LOG_PATH = Path("hospital_devices/log.txt")
REFRESH_MS = 10000  # milliseconds

# ---- Auto-refresh ----
autorefresh = getattr(st, "autorefresh", None) or getattr(st, "experimental_autorefresh", None)
if callable(autorefresh):
    autorefresh(interval=REFRESH_MS, key="log_refresh")
else:
    st.markdown(f'<meta http-equiv="refresh" content="{REFRESH_MS/1000}">', unsafe_allow_html=True)

# ---- Static UI ----
st.title("Zero Trust IoT Dashboard")
st.write("This is our real-time security monitor.")

# --- Current Time Placeholder (high up) ---
time_placeholder = st.empty()
time_placeholder.markdown(f"**Current time:** {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")

# Attack button (static)
st.subheader("Simulate Attacks")
colA, _ = st.columns(2)
if colA.button("BIG RED BUTTON"):
    subprocess.Popen([sys.executable, "attack_simulator.py", GATEWAY_URL])
    st.success("Attack simulator started! Sending spoofed requests to gateway!")

st.markdown("---")

# ---- Static headers ----
st.subheader("Summary Metrics")

# Static column titles
col1, col2, col3 = st.columns(3)
col1.write("**GRANTED**")
col2.write("**Denied Attempts**")
col3.write("**Suspicious Events**")

# Dynamic placeholders for numbers
granted_placeholder = col1.empty()
denied_placeholder = col2.empty()
suspicious_placeholder = col3.empty()

st.subheader("Live Security Logs")
logs_placeholder = st.empty()

# ---- Helper functions ----
def load_logs(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["timestamp", "device", "role", "target", "status", "message"])
    try:
        df = pd.read_csv(
            path,
            sep=",",
            names=["timestamp", "device", "role", "target", "status", "message"],
            dtype=str
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df
    except Exception as e:
        st.warning(f"Error reading log file: {e}")
        return pd.DataFrame(columns=["timestamp", "device", "role", "target", "status", "message"])

def highlight_row(row):
    color = ""
    status = str(row.get("status", ""))
    if status == "DENIED_SPOOFING":
        color = "background-color: #ff4d4d"
    elif status == "DENIED_POLICY":  # Highlight denied policy as suspicious
        color = "background-color: #ffcc00"
    elif status == "GRANTED":
        color = "background-color: #40a040"
    return [color] * len(row)

# ---- Refresh dynamic data ----
df = load_logs(LOG_PATH)

# Update metrics
granted_placeholder.metric("", df[df["status"] == "GRANTED"].shape[0])
denied_placeholder.metric("", df[df["status"] == "DENIED_SPOOFING"].shape[0])
suspicious_placeholder.metric("", df[df["status"] == "DENIED_POLICY"].shape[0])

# Update log table
if df.empty:
    logs_placeholder.info("No log file found or file is empty.")
else:
    logs_placeholder.dataframe(df.style.apply(highlight_row, axis=1), height=400)

# Update current time dynamically
time_placeholder.markdown(f"**Current time:** {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
