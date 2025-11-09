import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess
import sys

# Configs
GATEWAY_URL = "http://127.0.0.1:8000/vitals-db"  # domain URL
LOG_FILE = "log.txt"


st.title("Zero Trust IoT Dashboard")
st.write("This is our real-time security monitor.")
st.write("Current time:", datetime.now())

# Load Logs
try:
    df = pd.read_csv(
        "hospital_devices/log.txt",
        sep=",",
        names=["timestamp", "device", "role", "target", "status", "message"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
except FileNotFoundError:
    st.warning("No log file found. Waiting for gateway connection...")
    df = pd.DataFrame(columns=["timestamp", "device", "role", "target", "status", "message"])


# Summary
col1, col2, col3 = st.columns(3)
col1.metric(" Allowed Requests", df[df["status"] == "ALLOWED"].shape[0])
col2.metric(" Denied Attempts", df[df["status"] == "DENIED_SPOOFING"].shape[0])
col3.metric("️ Suspicious Events", df[df["status"] == "SUSPICIOUS"].shape[0])

# Color codes
def highlight_row(row):
    color = ""
    if row["status"] == "DENIED_SPOOFING":
        color = "background-color: #ff4d4d"
    elif row["status"] == "SUSPICIOUS":
        color = "background-color: #ffcc00"
    elif row["status"] == "ALLOWED":
        color = "background-color: #40a040"
    return [color] * len(row)

st.subheader(" Live Security Logs")
st.dataframe(df.style.apply(highlight_row, axis=1))

# Big red button
st.subheader("Simulate Attacks")
colA, colB = st.columns(2)

if colA.button("BIG RED BUTTON"):
    subprocess.Popen([sys.executable, "attack_simulator.py", GATEWAY_URL])
    st.success("Attack simulator started! Sending spoofed requests to gateway!")

